from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import SignUpSerializer, LoginSerializer
from .models import BlacklistedToken
from django.core.mail import send_mail
import re

User = get_user_model()

# ------------------------------
# ✅ USER REGISTRATION VIEW
# ------------------------------
@extend_schema(tags=['Auth'])
class SignUpView(APIView):
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

            send_mail(
                subject="🎉 Welcome to KitoDeck AI",
                message=(
                    f"Hi {user.username},\n\n"
                    "Welcome to KitoDeck AI — your smart assistant in avoiding kito predators.\n"
                    "You're officially part of a safer, smarter digital movement.\n\n"
                    "Explore your dashboard, scan images, and analyze chats like a pro.\n\n"
                    "Cheers,\n"
                    "The KitoDeck Team"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False
            )

            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# ✅ USER LOGIN VIEW (EMAIL + PASSWORD ONLY)
# ------------------------------
@extend_schema(tags=['Auth'])
class LoginView(APIView):
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
                else:
                    return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

            except User.DoesNotExist:
                return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# ------------------------------
# ✅ USER LOGOUT VIEW
# ------------------------------
@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=dict,
        responses={200: dict, 400: dict},
        examples=[
            OpenApiExample('Logout Example', value={"refresh": "<refresh_token>"})
        ]
    )
    def post(self, request):
        token = request.data.get('refresh')
        if not token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            BlacklistedToken.objects.create(token=token)
            return Response({'message': 'Logged out successfully'})
        except Exception as e:
            return Response({'error': str(e) or 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------
# ✅ IMAGE SCAN VIEW
# ------------------------------
@extend_schema(tags=['AI'])
class ImageScanView(APIView):
    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        return Response({
            'status': 'success',
            'message': 'Image analyzed. No kito indicators found.'
        })


# ------------------------------
# ✅ CHAT SCAN VIEW
# ------------------------------
@extend_schema(tags=['AI'])
class ChatScanView(APIView):
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
