# Third-party libraries
import hmac
import requests
from datetime import timedelta
from django.core import signing
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView,CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


# Local imports
from .throttles import RegisterThrottle, SendOtpThrottle, VerifyOtpThrottle,ForgetPasswordThrottle,VerifyForgetOtpThrottle,ResetPasswordThrottle,LoginThrottle, GoogleLoginThrottle
from .serializers import RegisterSerializer, VerifyOtpSerializer, SendOtpSerializer,CustomTokenObtainPairSerializer, ProfileSerializer, ForgotPasswordSerializer, VerifyForgotOtpSerializer, ResetPasswordSerializer
from .models import Profile, PendingUser
from .utils import hash_otp, OTP_EXPIRY_MINUTES, send_otp_email

MAX_OTP_ATTEMPTS = 5
MAX_OTP_RESENDS = 5
RESEND_COOLDOWN_SECONDS = 30


User = get_user_model()

# ===== Registration View =====
class RegisterView(CreateAPIView):
    queryset = PendingUser.objects.all()
    permission_classes = (AllowAny,)
    throttle_classes = [RegisterThrottle]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            email = serializer.validated_data["email"]

            pending_user, _ = PendingUser.objects.get_or_create(email=email)

            pending_user.username = serializer.validated_data.get(
                "username", pending_user.username
            )
            pending_user.name = serializer.validated_data.get(
                "name", pending_user.name
            )
            pending_user.role = serializer.validated_data.get(
                "role", pending_user.role
            )

            raw_password = serializer.validated_data["password"]
            pending_user.set_password(raw_password)
            pending_user.save()

        # 🔥 SINGLE SOURCE OF TRUTH FOR OTP
        success, msg = send_otp_email(
            obj=pending_user,
            email=pending_user.email,
            name=pending_user.name,
            purpose="account verification",
        )

        if not success:
            return Response(
                {"error": msg},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(
            {
                "message": "Pending registration created. Please verify OTP sent to your email.",
                "otp_status": msg,
            },
            status=status.HTTP_201_CREATED,
        )


# ===== OTP Sent View =====
class SendOtpView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = [SendOtpThrottle]

    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            pending_user = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response(
                {"error": "Invalid email or OTP."},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, msg = send_otp_email(
            obj=pending_user,
            email=pending_user.email,
            name=pending_user.name,
            purpose="account verification",
        )

        if not success:
            return Response({"error": msg}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response({"message": msg}, status=status.HTTP_200_OK)


# ===== OTP Verification View =====
class VerifyOtpView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = [VerifyOtpThrottle]

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            with transaction.atomic():
                pending_user = (
                    PendingUser.objects
                    .select_for_update()
                    .get(email=email)
                )

                #  Brute-force protection
                if pending_user.otp_attempts >= MAX_OTP_ATTEMPTS:
                    return Response(
                        {"error": "Too many invalid OTP attempts. Please request a new OTP."},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

                # OTP existence
                if not pending_user.otp_hash:
                    return Response(
                        {"error": "Invalid email or OTP."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # OTP expiry
                if (not pending_user.otp_created_at or timezone.now() - pending_user.otp_created_at > timedelta(minutes=OTP_EXPIRY_MINUTES)):
                    return Response(
                        {"error": "Invalid email or OTP."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # OTP match (constant-time)
                if not hmac.compare_digest(hash_otp(otp), pending_user.otp_hash):
                    pending_user.otp_attempts += 1
                    pending_user.save(update_fields=["otp_attempts"])
                    return Response(
                        {"error": "Invalid email or OTP."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Prevent duplicates
                if User.objects.filter(username=pending_user.username).exists():
                    return Response(
                        {"error": "Username already taken."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if User.objects.filter(email=pending_user.email).exists():
                    return Response(
                        {"error": "Email already registered. Please login."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Create real user
                user = User.objects.create_user(
                    username=pending_user.username,
                    email=pending_user.email,
                    password=pending_user.password,
                )

                profile = user.profile
                profile.name = pending_user.name
                profile.role = pending_user.role
                profile.is_verified = True
                profile.save()

                # Cleanup
                pending_user.delete()

        except PendingUser.DoesNotExist:
            return Response(
                {"error": "Invalid email or OTP."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # JWT outside transaction
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "OTP verified successfully! Registration complete.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": profile.role,
            },
            status=status.HTTP_200_OK,
        )


# ===== Login View =====
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]


# ===== Google Login View =====
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [GoogleLoginThrottle]

    def post(self, request):
        code = request.data.get("code")

        if not code:
            return Response(
                {"error": "Missing authorization code"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Exchange authorization code for tokens
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                return Response(
                    {
                        "error": "Failed to exchange authorization code",
                        "google_response": token_response.json(),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token_data = token_response.json()
            id_token_str = token_data.get("id_token")

            if not id_token_str:
                return Response(
                    {"error": "ID token not returned by Google"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify ID token
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

            email = id_info.get("email")
            name = id_info.get("name", email.split("@")[0])

            if not email:
                return Response(
                    {"error": "Email not found in Google token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create or get user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": email.split("@")[0]},
            )

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.name = name
            profile.role = "jobseeker"
            profile.save()

            # Issue JWT
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "id": user.id,
                    "name": profile.name,
                    "email": user.email,
                    "role": profile.role,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError:
            return Response(
                {"error": "Invalid Google ID token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": "Google login failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ===== Profile View =====
class ProfileAPIView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
    

# ===== Logout View=====
# class LogoutView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         refresh_token = request.data.get("refresh_token")
#         if not refresh_token:
#             return Response(
#                 {"error": "Refresh token is required"},
#                 status=400
#             )

#         try:
#             token = RefreshToken(refresh_token)
#             token.blacklist()
#         except TokenError:
#             return Response(
#                 {"error": "Invalid or expired token"},
#                 status=400
#             )

#         return Response(status=205)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"message": "Logged out"}, status=200)



# Token config
RESET_TOKEN_SALT = "password-reset"
RESET_TOKEN_MAX_AGE_SECONDS = 15 * 60


# ===== Forgot Password =====
class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = [ForgetPasswordThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()

        # Privacy protection
        if not user:
            return Response(
                {"message": "If an account exists, an OTP has been sent."},
                status=200
            )

        profile, _ = Profile.objects.get_or_create(user=user)

        # 🔥 ONE LINE DOES EVERYTHING (first-time + resend)
        success, msg = send_otp_email(
            obj=profile,
            email=user.email,
            name=profile.name or user.username,
            purpose="password reset",
        )

        if not success:
            return Response({"error": msg}, status=429)

        return Response({"message": msg}, status=200)


class VerifyForgotOtpView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = [VerifyForgetOtpThrottle]

    def post(self, request):
        serializer = VerifyForgotOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.only("id", "email", "username").filter(email=email).first()
        except User.DoesNotExist:
            return Response({"error": "Invalid request."}, status=400)

        profile, _ = Profile.objects.get_or_create(user=user)

        if not profile.otp_hash or not profile.otp_created_at:
            return Response({"error": "No OTP requested."}, status=400)

        # Expiry check
        if timezone.now() - profile.otp_created_at > timedelta(minutes=OTP_EXPIRY_MINUTES):
            return Response({"error": "OTP expired."}, status=400)

        # Attempt limit
        if profile.otp_attempts >= MAX_OTP_ATTEMPTS:
            return Response(
                {"error": "OTP attempts exceeded. Please request a new OTP."},
                status=400
            )

        # OTP match
        if hash_otp(otp) != profile.otp_hash:
            profile.otp_attempts += 1
            profile.save(update_fields=["otp_attempts"])
            return Response({"error": "Invalid OTP."}, status=400)

        # OTP verified → clear OTP
        profile.otp_hash = None
        profile.otp_created_at = None
        profile.otp_attempts = 0
        profile.save(update_fields=["otp_hash", "otp_created_at", "otp_attempts"])

        # Issue reset token
        reset_token = signing.dumps(
            {"email": email},
            salt=RESET_TOKEN_SALT
        )

        return Response(
            {
                "message": "OTP verified.",
                "reset_token": reset_token,
            },
            status=200
        )


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = [ResetPasswordThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["reset_token"]
        new_password = serializer.validated_data["password"]

        try:
            data = signing.loads(
                token,
                salt=RESET_TOKEN_SALT,
                max_age=RESET_TOKEN_MAX_AGE_SECONDS,
            )
        except signing.SignatureExpired:
            return Response({"error": "Reset token expired."}, status=400)
        except signing.BadSignature:
            return Response({"error": "Invalid reset token."}, status=400)

        email = data.get("email")
        if not email:
            return Response({"error": "Invalid reset token."}, status=400)

        try:
            user = User.objects.only("id", "email", "username").filter(email=email).first()
        except User.DoesNotExist:
            return Response({"error": "Invalid reset token."}, status=400)

        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=["password"])

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.otp_hash = None
            profile.otp_created_at = None
            profile.otp_attempts = 0
            profile.otp_resend_count = 0
            profile.save(
                update_fields=[
                    "otp_hash",
                    "otp_created_at",
                    "otp_attempts",
                    "otp_resend_count",
                ]
            )

        return Response(
            {
                "message": "Password reset successful. Please log in with your new password."
            },
            status=200,
        )
