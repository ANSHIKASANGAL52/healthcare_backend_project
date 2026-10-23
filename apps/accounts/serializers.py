from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for public user profile representation.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        style={'input_type': 'password'},
        help_text="Password must be at least 6 characters long."
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'password']
        read_only_fields = ['id']

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        if CustomUser.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_email

    def validate_name(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Name cannot be empty.")
        return stripped

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login and JWT token generation.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        user = authenticate(username=email, password=password)
        if not user:
            # Check if user exists to provide helpful error
            if not CustomUser.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError("Invalid email or password.")
            user_candidate = CustomUser.objects.filter(email__iexact=email).first()
            if not user_candidate.check_password(password):
                raise serializers.ValidationError("Invalid email or password.")
            if not user_candidate.is_active:
                raise serializers.ValidationError("User account is disabled.")
            user = user_candidate

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }
