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
        extra_kwargs = {
                'password': {'write_only': True},
                'email': {'required': True}
                }

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

        if instance.profile_pic:
            data['profile_pic'] = instance.profile_pic.url
        else:
            data['profile_pic'] = None

        if instance.resume:
            data['resume'] = instance.resume.url
        else:
            data['resume'] = None

        return data
