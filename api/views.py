from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    OpenApiTypes
)
from .serializers import UserSerializer
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Text analysis utilities
PROHIBITED_WORDS = [
    'kito', 'scam', 'fraud', 'cheat', 'fake', 'phishing',
    'blackmail', 'extortion', 'emergency', 'robbery', 'ambush',
    'setup', 'trap', 'gang', 'danger', 'threat', 'ransom',
    'boys', 'bait', 'lure', 'decoy', 'meet-up scam', 'dating scam',
    'robbery setup', 'catfish', 'not real', 'impersonating', 'kidnap',
    'hijack', 'attack', 'jump', 'danger zone', 'sketchy location'
]

SUSPICIOUS_PATTERNS = [
    r'send money', r'emergency situation', r'need help urgent',
    r'meet( me)? (at|in) .{1,20}(secluded|private|isolated)',
    r'don\'t tell anyone', r'keep (this|it) secret',
    r'change (of )?location', r'come alone', r'no friends',
    r'urgent meeting', r'quick meetup', r'need cash'
]

def send_welcome_email(user):
    """
    Send a beautifully styled HTML welcome email to new users
    """
    subject = 'Welcome to Our KitoDeck AI!'
    
    # Context for the email template
    context = {
        'username': user.username,
        'email': user.email,
        'support_email': 'support@kitodeck.ai',
        'platform_name': 'KitoDeck AI',
        'login_url': 'https://kitodeck.vercel.app/auth/login'
    }
    
    # Render HTML content
    html_content = render_to_string('emails/welcome.html', context)
    text_content = strip_tags(html_content)  # Fallback text version
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email='Welcome Team <no-reply@kitodeck.ai>',
        to=[user.email],
        reply_to=['support@kitodeck.ai']
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

def analyze_text_content(text):
    """Analyze text for kito scam indicators"""
    lower_text = text.lower()
    
    # Check for prohibited words
    found_words = [word for word in PROHIBITED_WORDS if word in lower_text]
    
    # Check for suspicious patterns
    pattern_matches = []
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, lower_text):
            pattern_matches.append(pattern)
    
    # Calculate risk score (0-1 scale)
    word_score = min(0.7, len(found_words) * 0.1)  # Max 0.7 from prohibited words
    pattern_score = min(0.3, len(pattern_matches) * 0.05)  # Max 0.3 from patterns
    total_score = word_score + pattern_score
    
    risk_level = "low"
    if total_score > 0.3:
        risk_level = "medium"
    if total_score > 0.6:
        risk_level = "high"
    
    return {
        'is_potential_kito': total_score > 0.2,
        'risk_score': total_score,
        'risk_level': risk_level,
        'prohibited_words': found_words,
        'suspicious_patterns': pattern_matches,
        'word_count': len(text.split()),
        'character_count': len(text)
    }

def check_conversation_signals(messages):
    """Check for kito warning signals in conversation patterns"""
    signals = {
        'urgent_meetup_request': False,
        'location_change_request': False,
        'rapid_escalation': False,
        'excessive_secrecy': False
    }
    
    # Check message timestamps for rapid escalation
    if len(messages) >= 3:
        timestamps = [msg.get('timestamp') for msg in messages if 'timestamp' in msg]
        if timestamps and all(timestamps):
            try:
                timestamps = [datetime.fromisoformat(ts) for ts in timestamps]
                time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                             for i in range(len(timestamps)-1)]
                
                # If average time between messages is less than 30 seconds and convo mentions meeting
                if sum(time_diffs)/len(time_diffs) < 30:
                    combined_text = " ".join([msg.get('content', '') for msg in messages])
                    if any(word in combined_text.lower() for word in ['meet', 'meeting', 'location', 'address']):
                        signals['rapid_escalation'] = True
            except (ValueError, TypeError):
                pass
    
    # Check for location changes or secrecy
    combined_text = " ".join([msg.get('content', '') for msg in messages]).lower()
    if any(phrase in combined_text for phrase in ['change location', 'different place', 'new address']):
        signals['location_change_request'] = True
    
    if any(phrase in combined_text for phrase in ['don\'t tell', 'our secret', 'between us', 'tell no one']):
        signals['excessive_secrecy'] = True
    
    if any(phrase in combined_text for phrase in ['meet now', 'come quickly', 'urgent meeting', 'asap']):
        signals['urgent_meetup_request'] = True
    
    return signals

# Authentication views
@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string'},
                'username': {'type': 'string', 'required': False}
            },
            'required': ['email', 'password']
        }
    },
    responses={
        201: OpenApiResponse(
            description='User created successfully',
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'tokens': {
                        'type': 'object',
                        'properties': {
                            'access': {'type': 'string'},
                            'refresh': {'type': 'string'}
                        }
                    },
                    'user': {
                        'type': 'object',
                        'properties': {
                            'email': {'type': 'string'},
                            'username': {'type': 'string'},
                            'id': {'type': 'integer'}
                        }
                    }
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'object'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    username = data.get('username', email.split('@')[0])  # Default to email prefix if username not provided

    # Validation
    errors = {}
    if not email:
        errors['email'] = ['Email is required']
    if not password:
        errors['password'] = ['Password is required']
    elif len(password) < 8:
        errors['password'] = ['Password must be at least 8 characters']
    
    if errors:
        return Response({
            'error': 'Validation failed',
            'details': errors
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'Email already registered',
            'details': {'email': ['This email is already in use']}
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        refresh = RefreshToken.for_user(user)
        
        # Send welcome email (async in production with Celery)
        send_welcome_email(user)

        return Response({
            'message': 'Sign up successful!',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Account creation failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string'}
            },
            'required': ['email', 'password']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Login successful',
            response={
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'email': {'type': 'string'},
                            'username': {'type': 'string'},
                            'id': {'type': 'integer'}
                        }
                    }
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        ),
        401: OpenApiResponse(
            description='Unauthorized',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data 
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response({
            'error': 'Email and password are required',
            'details': 'Both fields must be provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            return Response({
                'error': 'Invalid credentials',
                'details': 'Incorrect password'
            }, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'email': user.email,
                'username': user.username,
                'id': user.id
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'Invalid credentials',
            'details': 'No account found with this email'
        }, status=status.HTTP_401_UNAUTHORIZED)

@extend_schema(
    description='Log out a user by blacklisting their refresh token',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'JWT refresh token'}
            },
            'required': ['refresh']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Successfully logged out',
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        # Also log out from the session
        logout(request)
        
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Failed to logout',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    description='Get current user details',
    responses={
        200: OpenApiResponse(
            description='User details',
            response=UserSerializer
        ),
        401: OpenApiResponse(
            description='Unauthorized',
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Functional views
@extend_schema(
    description='Analyze text using natural language processing',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'text': {'type': 'string', 'description': 'Text to analyze'}
            },
            'required': ['text']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Analysis results',
            response={
                'type': 'object',
                'properties': {
                    'sentiment': {'type': 'string'},
                    'entities': {'type': 'array', 'items': {'type': 'object'}},
                    'summary': {'type': 'string'}
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_text(request):
    text = request.data.get('text')
    
    if not text:
        return Response({
            'error': 'Text is required for analysis'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Example analysis result (would use NLP libraries in real implementation)
    analysis = {
        'sentiment': 'positive' if len(text) % 2 == 0 else 'negative',
        'entities': [
            {'type': 'PERSON', 'text': 'Sample Person'} if 'person' in text.lower() else {},
            {'type': 'LOCATION', 'text': 'Sample Location'} if 'location' in text.lower() else {}
        ],
        'summary': text[:100] + '...' if len(text) > 100 else text
    }
    
    return Response(analysis, status=status.HTTP_200_OK)

@extend_schema(
    description='Scan image for text and objects',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {'type': 'string', 'format': 'binary'}
            },
            'required': ['image']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Scan results',
            response={
                'type': 'object',
                'properties': {
                    'text': {'type': 'string'},
                    'objects': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_image(request):
    if 'image' not in request.FILES:
        return Response({
            'error': 'Image file is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Example scan result (would use OCR/image recognition in real implementation)
    results = {
        'text': 'Sample extracted text from image',
        'objects': ['object1', 'object2', 'object3']
    }
    
    return Response(results, status=status.HTTP_200_OK)

@extend_schema(
    description='Example protected endpoint',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'data': {'type': 'object', 'description': 'Any data to process'}
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description='Processed data',
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user': {'type': 'string'},
                    'received_data': {'type': 'object'}
                }
            }
        ),
        401: OpenApiResponse(
            description='Unauthorized',
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_data(request):
    return Response({
        'message': 'Data processed successfully',
        'user': request.user.username,
        'received_data': request.data
    }, status=status.HTTP_200_OK)

# Kito protection views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_message(request):
    """Analyze user message for potential kito scam indicators"""
    text = request.data.get('text')
    
    if not text:
        return Response({
            'error': 'Text is required for analysis'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    analysis = analyze_text_content(text)
    
    # Log high-risk messages for further review if risk is high
    if analysis['risk_level'] == 'high':
        logger.warning(f"High risk message detected: {text[:100]}... - Score: {analysis['risk_score']}")
    
    return Response(analysis, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_conversation_safety(request):
    """Analyze a conversation for kito warning signs"""
    conversation = request.data.get('messages', [])
    user_id = request.data.get('user_id')
    
    if not conversation or not user_id:
        return Response({
            'error': 'Messages and user_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Combine messages for overall analysis
    combined_text = " ".join([msg.get('content', '') for msg in conversation])
    analysis = analyze_text_content(combined_text)
    
    # Add conversation-specific checks
    conversation_signals = check_conversation_signals(conversation)
    analysis.update(conversation_signals)
    
    # Store safety report for this conversation
    SafetyReport.objects.create(
        user_id=user_id,
        conversation_id=request.data.get('conversation_id'),
        risk_score=analysis['risk_score'],
        risk_level=analysis['risk_level'],
        details=json.dumps(analysis)
    )
    
    return Response(analysis, status=status.HTTP_200_OK)

@extend_schema(
    description='Scan image for text to detect kito warning signs',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {'type': 'string', 'format': 'binary'}
            },
            'required': ['image']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Scan results with kito analysis',
            response={
                'type': 'object',
                'properties': {
                    'extracted_text': {'type': 'string'},
                    'kito_analysis': {'type': 'object'},
                    'risk_level': {'type': 'string'}
                }
            }
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_image_for_safety(request):
    """Scan image for text and analyze it for kito indicators"""
    if 'image' not in request.FILES:
        return Response({
            'error': 'Image file is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    image = request.FILES['image']
    
    try:
        # Simulate OCR text extraction (replace with actual OCR implementation)
        extracted_text = "Sample extracted text for demonstration"
        
        # Process the extracted text for kito indicators
        kito_analysis = analyze_text_content(extracted_text)
        
        return Response({
            'extracted_text': extracted_text,
            'kito_analysis': kito_analysis,
            'risk_level': kito_analysis['risk_level']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error processing image: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)