from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'name', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        name = validated_data.pop('name')
        role = validated_data.pop('role')
        user = User.objects.create_user(**validated_data)
        user.profile.name = name
        user.profile.role = role
        user.profile.save()
        return user

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

# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email', read_only=True)
#     profile_pic_url = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = Profile
#         fields = [
#             'id', 'user', 'role', 'name', 'email', 'phone', 'education', 'location',
#             'dob', 'gender', 'skills', 'profile_pic', 'profile_pic_url', 'resume'
#         ]
#         read_only_fields = ['user', 'role', 'email']

#     def get_profile_pic_url(self, obj):
#         request = self.context.get('request')
#         if obj.profile_pic and hasattr(obj.profile_pic, 'url'):
#             return request.build_absolute_uri(obj.profile_pic.url)
#         return None

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         # Optional: rename `profile_pic_url` to `profile_pic` in output
#         if data.get('profile_pic_url'):
#             data['profile_pic'] = data.pop('profile_pic_url')
#         return data

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    resume_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'role', 'name', 'email', 'phone', 'education', 'location',
            'dob', 'gender', 'skills', 'profile_pic', 'profile_pic_url', 'resume', 'resume_url'
        ]
        read_only_fields = ['user', 'role', 'email']

    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url  # Cloudinary already gives full URL
        return None

    def get_resume_url(self, obj):
        if obj.resume:
            return obj.resume.url  # Cloudinary already gives full URL
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Replace profile_pic field with its full URL
        if data.get('profile_pic_url'):
            data['profile_pic'] = data.pop('profile_pic_url')
        else:
            data['profile_pic'] = None

        # Replace resume field with its full URL
        if data.get('resume_url'):
            data['resume'] = data.pop('resume_url')
        else:
            data['resume'] = None

        return data
