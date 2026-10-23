from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer


class RegisterView(APIView):
    """
    Register a new user with name, email, and password.
    Returns the created user and authentication tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        summary="Register a new user",
        description="Creates a new user account with name, email, and password.",
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(description="User registered successfully"),
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "success": True,
                    "message": "User registered successfully.",
                    "data": {
                        "user": UserSerializer(user).data,
                        "tokens": {
                            "access": str(refresh.access_token),
                            "refresh": str(refresh)
                        }
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "success": False,
                "message": "Registration failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    """
    Log in an existing user with email and password.
    Returns JWT access and refresh tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(
        summary="Log in user",
        description="Authenticates credentials and returns JWT access and refresh tokens.",
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful"),
            400: OpenApiResponse(description="Invalid credentials or bad request")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.validated_data['tokens']
            return Response(
                {
                    "success": True,
                    "message": "Login successful.",
                    "data": {
                        "user": UserSerializer(user).data,
                        "tokens": tokens
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "success": False,
                "message": "Login failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
