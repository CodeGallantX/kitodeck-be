from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    OpenApiTypes
)
from .serializers import UserSerializer

def send_welcome_email(user):
    """
    Send a beautifully styled HTML welcome email to new users
    """
    subject = 'Welcome to Our Platform!'
    
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
            },
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        "message": "Sign up successful!",
                        "tokens": {
                            "access": "eyJhbGciOiJIUz...",
                            "refresh": "eyJhbGciOiJIUz..."
                        },
                        "user": {
                            "email": "user@example.com",
                            "username": "user123",
                            "id": 1
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'object'}
                }
            },
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={
                        "error": "Validation failed",
                        "details": {
                            "email": ["This email is already registered"],
                            "password": ["This password is too common"]
                        }
                    }
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            'Example Request',
            value={
                "email": "user@example.com",
                "password": "securepassword123",
                "username": "optional_username"
            }
        )
    ],
    description='Register a new user account'
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
            },
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        "access": "eyJhbGciOiJIUz...",
                        "refresh": "eyJhbGciOiJIUz...",
                        "user": {
                            "email": "user@example.com",
                            "username": "user123",
                            "id": 1
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={"error": "Email and password are required"}
                )
            ]
        ),
        401: OpenApiResponse(
            description='Unauthorized',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            },
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={"error": "Invalid credentials", "details": "No account found with this email"}
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            'Example Request',
            value={
                "email": "user@example.com",
                "password": "securepassword123"
            }
        )
    ],
    description='Authenticate user and return JWT tokens'
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
            },
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={"message": "Successfully logged out"}
                )
            ]
        ),
        400: OpenApiResponse(
            description='Bad Request',
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={"error": "Refresh token is required"}
                )
            ]
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