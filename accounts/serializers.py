import hashlib
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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

        otp_hash = hashlib.sha256(data["otp"].encode()).hexdigest()
        if pending_user.otp_hash != otp_hash:
            pending_user.otp_attempts += 1
            pending_user.save(update_fields=["otp_attempts"])
            raise serializers.ValidationError("Invalid OTP.")

        if timezone.now() - pending_user.otp_created_at > timedelta(minutes=10):
            raise serializers.ValidationError("OTP expired.")

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
            'token': data['access'],
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
        data['profile_pic'] = instance.profile_pic.url if instance.profile_pic else None
        data['resume'] = instance.resume.url if instance.resume else None
        return data


# ===== Forgot Password =====
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyForgotOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResendForgotOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")

        if not hasattr(user, "profile"):
            raise serializers.ValidationError("Profile not found for this user.")

        attrs["user"] = user
        return attrs

class ResetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
