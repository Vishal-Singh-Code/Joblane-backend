from rest_framework import serializers
from jobs.models import Application
from accounts.serializers import ProfileSerializer
from jobs.serializers.common_serializers import JobBasicSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = ProfileSerializer(read_only=True)
    job = JobBasicSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'applied_at', 'status']

class BasicApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source='applicant.name')
    applicant_email = serializers.EmailField(source='applicant.user.email')
    status = serializers.CharField()

    class Meta:
        model = Application
        fields = ['id', 'applicant_name', 'applicant_email', 'status' , 'applied_at']

