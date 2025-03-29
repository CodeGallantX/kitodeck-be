from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
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

# Example for the signup endpoint
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
                    'error': {'type': 'string'}
                }
            },
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={"error": "Email already registered"}
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
    """
    Register a new user
    
    Parameters:
    - email (string): User's email address (will be used as username)
    - password (string): User's password
    - username (string, optional): Custom username
    
    Returns:
    - On success: 201 Created with success message and tokens
    - On failure: 400 Bad Request with error message
    """
    data = request.data
    email = data.get('email')
    password = data.get('password')
    username = data.get('username', email)  # Default to email if username not provided

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = User.objects.create_user(username=username, email=email, password=password)

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    # Send confirmation email
    send_mail(
        'Welcome!',
        f'Hello {email},\n\nThank you for signing up.',
        'no-reply@yourdomain.com',
        [email],
        fail_silently=False,
    )

    return Response({
        'message': 'Sign up successful!',
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        },
        'user': {
            'email': user.email,
            'username': user.username,
            'id': user.id
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return JWT tokens
    
    Parameters:
    - email (string): User's email
    - password (string): User's password
    
    Returns:
    - On success: 200 OK with tokens and user data
    - On failure: 401 Unauthorized
    """
    data = request.data 
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=email, password=password)

    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    """
    Get current user details
    
    Requires:
    - Valid JWT token in Authorization header
    
    Returns:
    - 200 OK with user details
    """
    user = request.user
    return Response({
        'email': user.email,
        'username': user.username,
        'id': user.id,
        'is_staff': user.is_staff
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_data(request):
    """
    Example protected endpoint
    
    Requires:
    - Valid JWT token
    
    Parameters:
    - Any JSON data
    
    Returns:
    - 200 OK with processed data
    """
    return Response({
        'message': 'Data processed',
        'user': request.user.username,
        'received_data': request.data
    }, status=status.HTTP_200_OK)