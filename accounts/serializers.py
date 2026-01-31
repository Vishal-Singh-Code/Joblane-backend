import hashlib
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password

from .models import Profile, PendingUser

User = get_user_model()

# ===== Register =====
class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, write_only=True)
    email = serializers.EmailField(validators=[])

    class Meta:
        model = PendingUser
        fields = ('username', 'email', 'password', 'name', 'role')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "Email already registered. Please login."
            })

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                "username": "Username already taken."
            })

        return attrs

    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        email = validated_data["email"]
        username = validated_data.get("username")

        if PendingUser.objects.filter(username=username).exclude(email=email).exists():
            raise serializers.ValidationError({
                "username": "Username already in use."
            })

        try:
            pending_user = PendingUser.objects.get(email=email)
            pending_user.username = validated_data.get("username", pending_user.username)
            pending_user.name = validated_data.get("name", pending_user.name)
            pending_user.role = validated_data.get("role", pending_user.role)
            pending_user.set_password(raw_password)
            pending_user.save()
        except PendingUser.DoesNotExist:
            pending_user = PendingUser(**validated_data)
            pending_user.set_password(raw_password)
            pending_user.save()

        return pending_user

# ===== OTP Request =====
class SendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

# ===== OTP Verification =====
class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            pending_user = PendingUser.objects.get(email=data["email"])
        except PendingUser.DoesNotExist:
            raise serializers.ValidationError("No pending user found with this email.")

        if not pending_user.otp_created_at:
            raise serializers.ValidationError("OTP not requested.")

        if timezone.now() - pending_user.otp_created_at > timedelta(minutes=10):
            raise serializers.ValidationError("OTP expired.")

        otp_hash = hashlib.sha256(data["otp"].encode()).hexdigest()
        if pending_user.otp_hash != otp_hash:
            pending_user.otp_attempts += 1
            pending_user.save(update_fields=["otp_attempts"])
            raise serializers.ValidationError("Invalid OTP.")

        return data


# ===== Login =====
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        profile = self.user.profile

        return {
            'id': self.user.id,
            'name': profile.name,
            'email': self.user.email,
            'role': profile.role,
            'access': data['access'],
            'refresh': data['refresh']  
        }


# ===== Profile =====
class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'role', 'name', 'email', 'phone', 'education', 'location',
            'dob', 'gender', 'skills', 'profile_pic', 'resume'
        ]
        read_only_fields = ['user', 'role', 'email']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        if instance.profile_pic and request:
            data["profile_pic"] = request.build_absolute_uri(instance.profile_pic.url)
        else:
            data["profile_pic"] = None

        if instance.resume and request:
            data["resume"] = request.build_absolute_uri(instance.resume.url)
        else:
            data["resume"] = None

        return data

    
    def validate_profile_pic(self, file):
        if file.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Avatar size must be ≤ 2MB")

        if not file.content_type.startswith("image/"):
            raise serializers.ValidationError("Only image files are allowed")

        return file
    
    def validate_resume(self, file):
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume must be ≤ 5MB")

        if not file.name.lower().endswith((".pdf", ".doc", ".docx")):
            raise serializers.ValidationError("Only PDF or DOC files are allowed")

        return file


# ===== Forgot Password =====
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyForgotOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )

        # 🔐 Django password validation
        validate_password(attrs["password"])

        return attrs
