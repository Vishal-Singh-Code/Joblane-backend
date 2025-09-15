# Third-party libraries
import requests
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser

# Local imports
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, ProfileSerializer
from accounts.models import Profile

User = get_user_model()


# class RegisterView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     permission_classes = (AllowAny,)
#     serializer_class = RegisterSerializer

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         refresh = RefreshToken.for_user(user)
#         role = user.profile.role

#         return Response({
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#             "role": role
#         }, status=status.HTTP_201_CREATED)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Mark as unverified (until OTP is confirmed)
        user.profile.is_verified = False
        user.profile.save()

        # Send OTP email
        success, msg = send_otp_email(user, purpose="account verification")

        return Response({
            "message": "User registered successfully. Please verify OTP sent to your email.",
            "otp_status": msg
        }, status=status.HTTP_201_CREATED)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Missing access_token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
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

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=205)
        except Exception as e:
            return Response(status=400)





from rest_framework.views import APIView
from .serializers import VerifyOtpSerializer
from .utils import hash_otp, OTP_EXPIRY_MINUTES
from django.utils import timezone

class VerifyOtpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
            profile = user.profile
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # OTP checks
        if not profile.otp_hash:
            return Response({"error": "No OTP requested"}, status=400)

        if timezone.now() - profile.otp_created_at > timezone.timedelta(minutes=OTP_EXPIRY_MINUTES):
            return Response({"error": "OTP expired"}, status=400)

        if hash_otp(otp) != profile.otp_hash:
            profile.otp_attempts += 1
            profile.save()
            return Response({"error": "Invalid OTP"}, status=400)

        # Success
        profile.is_verified = True
        profile.otp_hash = None
        profile.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "OTP verified successfully!",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": profile.role
        })


from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import SendOtpSerializer
from .utils import send_otp_email


class SendOtpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

        success, msg = send_otp_email(user, purpose="account verification")

        if success:
            return Response({"message": msg}, status=status.HTTP_200_OK)
        else:
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
