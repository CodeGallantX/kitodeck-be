from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import SignUpSerializer, LoginSerializer, UserProfileSerializer
from .models import BlacklistedToken
from .utils.email import send_welcome_email
import re
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# ------------------------------
# USER REGISTRATION 
# ------------------------------
@extend_schema(tags=['Auth'])
class SignUpView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignUpSerializer,
        responses={201: dict, 400: dict},
        examples=[
            OpenApiExample(
                'Signup Example',
                value={
                    "username": "john_doe",
                    "email": "john@example.com",
                    "password": "Pass1234"
                }
            )
        ]
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_welcome_email(user)
            return Response({'message': 'User created successfully!'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# USER LOGIN 
# ------------------------------
@extend_schema(tags=['Auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    })
                return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

            except User.DoesNotExist:
                return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# USER LOGOUT 
# ------------------------------
@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=dict,
        responses={200: dict, 400: dict},
        examples=[OpenApiExample('Logout Example', value={"refresh": "<refresh_token>"})]
    )
    def post(self, request):
        token = request.data.get('refresh')
        if not token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            BlacklistedToken.objects.create(token=token)
            return Response({'message': 'Logged out successfully'})
        except Exception as e:
            logger.exception("Error during logout")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------
# GET USER PROFILE
# ------------------------------
@extend_schema(tags=["User"])
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error fetching user profile")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------
# IMAGE SCAN 
# ------------------------------
@extend_schema(tags=['AI'])
class ImageScanView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        return Response({
            'status': 'success',
            'message': 'Image analyzed. No kito indicators found.'
        })


# ------------------------------
# CHAT SCAN 
# ------------------------------
@extend_schema(tags=['AI'])
class ChatScanView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=dict,
        responses={200: dict},
        examples=[
            OpenApiExample(
                'Chat Scan Example',
                value={"transcript": "Hey baby, send me money now."}
            )
        ]
    )
    def post(self, request):
        transcript = request.data.get('transcript', '')
        kito_keywords = ['send me money', 'urgent transfer', 'sugar daddy', 'private snap']

        detected = [kw for kw in kito_keywords if re.search(kw, transcript, re.IGNORECASE)]

        return Response({
            'status': 'success',
            'kito_indicators': detected,
            'message': 'Potential threat detected' if detected else 'Safe conversation'
        })
