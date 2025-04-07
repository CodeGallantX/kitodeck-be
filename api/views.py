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
    data = request.data
    email = data.get('email')
    password = data.get('password')
    username = data.get('username', email)  # Default to email if username not provided

    if not email or not password:
        return Response({'error': 'Email and password are required'}, 
                      status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, 
                      status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    refresh = RefreshToken.for_user(user)

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
            'id': user.id,
            'email': user.email,
            'username': user.username
        }
    }, status=status.HTTP_201_CREATED)

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
                    'error': {'type': 'string'}
                }
            },
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={"error": "Invalid credentials"}
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
        return Response({'error': 'Email and password are required'}, 
                      status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        user = authenticate(username=user.username, password=password)
    except User.DoesNotExist:
        user = None

    if user is None:
        error_msg = 'Invalid credentials'
        if not User.objects.filter(email=email).exists():
            error_msg = 'No account found with this email'
        return Response({'error': error_msg}, 
                      status=status.HTTP_401_UNAUTHORIZED)

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

@extend_schema(
    description='Get current user details',
    responses={
        200: OpenApiResponse(
            description='User details',
            response={
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'username': {'type': 'string'},
                    'id': {'type': 'integer'},
                    'is_staff': {'type': 'boolean'}
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
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    user = request.user
    return Response({
        'email': user.email,
        'username': user.username,
        'id': user.id,
        'is_staff': user.is_staff
    }, status=status.HTTP_200_OK)

@extend_schema(
    description='Example protected endpoint',
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
        'message': 'Data processed',
        'user': request.user.username,
        'received_data': request.data
    }, status=status.HTTP_200_OK)