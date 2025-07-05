# Third-party libraries
import requests
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser

# Local imports
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, ProfileSerializer
from accounts.models import Profile

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        role = user.profile.role

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": role
        }, status=status.HTTP_201_CREATED)

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Missing access_token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch user info from Google API
            user_info = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                params={"access_token": access_token}
            ).json()

            email = user_info.get("email")
            name = user_info.get("name", email.split("@")[0])

            if not email:
                return Response({"error": "Email not found in Google data"}, status=400)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": email.split("@")[0]}
            )

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.name = name
            profile.role = "jobseeker"
            profile.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                'id': user.id,
                'name': profile.name,
                'email': user.email,
                'role': profile.role,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })

        except Exception as e:
            return Response({"error": "Google login failed", "details": str(e)}, status=500)

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


