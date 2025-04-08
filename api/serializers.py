from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'is_staff', 'date_joined']

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
        
    def validate_password(self, value):
        validate_password(value)
        return value
        
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer for login credentials"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class TokenSerializer(serializers.Serializer):
    """Serializer for JWT tokens"""
    refresh = serializers.CharField()
    access = serializers.CharField()

class TextAnalysisSerializer(serializers.Serializer):
    """Serializer for text analysis requests"""
    text = serializers.CharField(required=True)

class ImageScanSerializer(serializers.Serializer):
    """Serializer for image scanning requests"""
    image = serializers.ImageField(required=True)