# Third-party libraries
import requests
from datetime import timedelta
from django.core import signing
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser

# Local imports
from .serializers import RegisterSerializer, VerifyOtpSerializer, SendOtpSerializer,CustomTokenObtainPairSerializer, ProfileSerializer, ForgotPasswordSerializer, VerifyForgotOtpSerializer, ResendForgotOtpSerializer, ResetPasswordSerializer
from .models import Profile, PendingUser
from .utils import hash_otp, OTP_EXPIRY_MINUTES, send_otp_email, generate_otp
from .utils import send_otp_email_async



User = get_user_model()

# ===== Registration View =====
class RegisterView(generics.CreateAPIView):
    queryset = PendingUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Check if PendingUser already exists
        pending_user, created = PendingUser.objects.get_or_create(email=email)
        # Update fields if user is already pending
        pending_user.username = serializer.validated_data.get("username", pending_user.username)
        pending_user.name = serializer.validated_data.get("name", pending_user.name)
        pending_user.role = serializer.validated_data.get("role", pending_user.role)
        raw_password = serializer.validated_data["password"]
        pending_user.set_password(raw_password)
        pending_user.save()

        # Send OTP
        # success, msg = send_otp_email(
        #     obj=pending_user,
        #     email=pending_user.email,
        #     name=pending_user.name,
        #     purpose="account verification"
        # )
        send_otp_email_async(
        obj=pending_user,
        email=pending_user.email,
        name=pending_user.name,
        purpose="account verification"
        )
        success, msg = True, "OTP sent successfully."

        return Response({
            "message": "Pending registration created. Please verify OTP sent to your email.",
            "otp_status": msg
        }, status=status.HTTP_201_CREATED)


# ===== OTP Verification View =====
class VerifyOtpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        # Fetch pending user
        try:
            pending_user = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"non_field_errors": ["No pending user found with this email."]}, status=404)

        # OTP validation
        if not pending_user.otp_hash:
            return Response({"error": "No OTP requested."}, status=400)

        if timezone.now() - pending_user.otp_created_at > timedelta(minutes=OTP_EXPIRY_MINUTES):
            return Response({"error": "OTP expired."}, status=400)

        if hash_otp(otp) != pending_user.otp_hash:
            pending_user.otp_attempts += 1
            pending_user.save(update_fields=["otp_attempts"])
            return Response({"error": "Invalid OTP."}, status=400)

        # Check for existing User with same username/email
        if User.objects.filter(username=pending_user.username).exists():
            return Response({"error": "Username already taken. Choose another."}, status=400)
        if User.objects.filter(email=pending_user.email).exists():
            return Response({"error": "Email already registered. Please login."}, status=400)

        # OTP verified → create real User
        user = User.objects.create(
            username=pending_user.username,
            email=pending_user.email,
            password=pending_user.password,  
            is_active=True                   
        )

        # Update Profile
        profile = user.profile
        profile.name = pending_user.name
        profile.role = pending_user.role
        profile.is_verified = True
        profile.save()

        # Delete PendingUser
        pending_user.delete()

        # Generate JWT
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "OTP verified successfully! Registration complete.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": profile.role
        })


# ===== OTP Sent View =====
class SendOtpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            pending_user = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"error": "No pending registration found"}, status=404)

        # success, msg = send_otp_email(
        #     obj=pending_user,
        #     email=pending_user.email,
        #     name=pending_user.name,
        #     purpose="account verification"
        # )
        send_otp_email_async(
        obj=pending_user,
        email=pending_user.email,
        name=pending_user.name,
        purpose="account verification"
        )
        success, msg = True, "OTP sent successfully."


        if success:
            return Response({"message": msg}, status=status.HTTP_200_OK)
        else:
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        
    
# ===== Login View =====
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ===== Google Login View =====
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


# ===== Profile View =====
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


# ===== Logout View=====
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


# Token config
RESET_TOKEN_SALT = "password-reset"
RESET_TOKEN_MAX_AGE_SECONDS = 15 * 60  # 15 minutes (adjust as desired)


# ===== Forgot Password =====
class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            profile = user.profile
        except User.DoesNotExist:
            # Privacy: don't leak existence of account
            return Response({"message": "If an account exists, an OTP has been sent."})

        # Generate OTP
        otp = generate_otp()
        profile.otp_hash = hash_otp(otp)
        profile.otp_created_at = timezone.now()
        profile.otp_attempts = 0
        profile.otp_resend_count = 0
        profile.save(update_fields=["otp_hash", "otp_created_at", "otp_attempts", "otp_resend_count"])

        # send_otp_email(obj=profile, email=user.email, name=profile.name or user.username, purpose="password reset")
        send_otp_email_async(profile, user.email, profile.name or user.username, purpose="password reset")


        return Response({"message": "If an account exists, an OTP has been sent."})

class VerifyForgotOtpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        
        serializer = VerifyForgotOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(email=email)
            profile = user.profile
        except User.DoesNotExist:
            return Response({"non_field_errors": ["Invalid request."]}, status=400)

        if not profile.otp_hash:
            return Response({"error": "No OTP requested."}, status=400)

        if timezone.now() - profile.otp_created_at > timedelta(minutes=OTP_EXPIRY_MINUTES):
            return Response({"error": "OTP expired."}, status=400)

        if hash_otp(otp) != profile.otp_hash:
            profile.otp_attempts += 1
            profile.save(update_fields=["otp_attempts"])
            return Response({"error": "Invalid OTP."}, status=400)

        # OTP verified → clear OTP
        profile.otp_hash = None
        profile.otp_created_at = None
        profile.otp_attempts = 0
        profile.save(update_fields=["otp_hash", "otp_created_at", "otp_attempts"])

        # Create signed reset token
        reset_token = signing.dumps({"email": email}, salt=RESET_TOKEN_SALT)
        return Response({"message": "OTP verified.", "reset_token": reset_token})

class ResendForgotOtpView(generics.GenericAPIView):
    serializer_class = ResendForgotOtpSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        profile = user.profile

        # Rate limit check
        if profile.otp_resend_count >= 5 and profile.last_otp_sent_at and \
           (timezone.now() - profile.last_otp_sent_at).seconds < 3600:
            return Response({"error": "Too many OTP requests. Try again later."}, status=429)

        # Call utils — this will generate OTP, hash it, save, send mail
        # success, msg = send_otp_email(profile, user.email, profile.name or user.username, purpose="password reset")
        send_otp_email_async(profile, user.email, profile.name or user.username, purpose="password reset")
        success, msg = True, "OTP sent successfully."


        if not success:
            return Response({"error": msg}, status=400)

        return Response({"message": msg})

class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["reset_token"]
        new_password = serializer.validated_data["password"]

        try:
            data = signing.loads(token, salt=RESET_TOKEN_SALT, max_age=RESET_TOKEN_MAX_AGE_SECONDS)
        except signing.SignatureExpired:
            return Response({"error": "Reset token expired."}, status=400)
        except signing.BadSignature:
            return Response({"error": "Invalid reset token."}, status=400)

        email = data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid reset token."}, status=400)

        user.set_password(new_password)
        user.save()

        profile = user.profile
        profile.otp_hash = None
        profile.otp_created_at = None
        profile.otp_attempts = 0
        profile.save(update_fields=["otp_hash", "otp_created_at", "otp_attempts"])

        return Response({"message": "Password reset successful. Please log in with your new password."})