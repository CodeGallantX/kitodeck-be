from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow public access
def sign_up(request):
    data = request.data  # ✅ DRF handles JSON parsing
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = User.objects.create_user(username=email, email=email, password=password)

    # Send confirmation email
    send_mail(
        'Welcome to Our Platform!',
        f'Hello {email},\n\nThank you for signing up. Your account has been created successfully.',
        'no-reply@yourdomain.com',
        [email],
        fail_silently=False,
    )

    return Response({'message': 'Sign-up successful. Check your email!', 'user': email}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data  # ✅ DRF handles JSON parsing
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
        'refresh': str(refresh)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])  # ✅ Allows only POST requests
def process_data(request):
    data = request.data  # DRF automatically handles JSON parsing

    if not data:
        return Response({'error': 'No data provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Process the data (dummy logic)
    response_message = "Data processed successfully"

    return Response({'message': response_message}, status=status.HTTP_200_OK)
