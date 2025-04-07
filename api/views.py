from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .serializers import UserSerializer
from .utils.analysis import analyze_text_content

User = get_user_model()

# Email Utility Functions
def send_welcome_email(user):
    """Send styled welcome email to new users"""
    subject = 'Welcome to KitoDeck!'
    context = {
        'username': user.username,
        'email': user.email,
        'support_email': 'support@kitodeck.com',
        'platform_name': 'KitoDeck',
        'login_url': 'https://yourdomain.com/login'
    }
    
    html_content = render_to_string('emails/welcome.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email='KitoDeck Team <no-reply@kitodeck.com>',
        to=[user.email],
        reply_to=['support@kitodeck.com']
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

# Authentication Views
@extend_schema(
    tags=['Authentication'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string'},
                'username': {'type': 'string'}
            },
            'required': ['email', 'password']
        }
    },
    responses={
        201: OpenApiResponse(
            description='User created successfully',
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
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')
        username = data.get('username', email.split('@')[0])

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_409_CONFLICT
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        refresh = RefreshToken.for_user(user)
        send_welcome_email(user)

        return Response({
            'message': 'Sign up successful!',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            },
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': 'Account creation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    tags=['Authentication'],
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
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        user = authenticate(username=user.username, password=password)
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })

    except User.DoesNotExist:
        return Response(
            {'error': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@extend_schema(tags=['Authentication'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_205_RESET_CONTENT
        )
    
    except Exception as e:
        return Response(
            {'error': 'Logout failed', 'details': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# User Profile Views
@extend_schema(tags=['User'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    user = request.user
    return Response(UserSerializer(user).data)

# Analysis Views
@extend_schema(
    tags=['Analysis'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'text': {'type': 'string'}
            },
            'required': ['text']
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_text(request):
    text = request.data.get('text', '')
    if not text:
        return Response(
            {'error': 'Text is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    analysis = analyze_text_content(text)
    return Response(analysis)

@extend_schema(tags=['Analysis'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_image(request):
    image = request.FILES.get('image')
    if not image:
        return Response(
            {'error': 'Image is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Dummy implementation - replace with real image analysis
    return Response({
        'is_safe': True,
        'analysis': 'Image appears safe (demo)',
        'width': 800,
        'height': 600,
        'format': image.content_type.split('/')[-1].upper()
    })