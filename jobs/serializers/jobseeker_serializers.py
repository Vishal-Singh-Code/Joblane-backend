from rest_framework import serializers
from jobs.models import Application
from jobs.serializers.common_serializers import JobBasicSerializer


class AppliedJobSerializer(serializers.ModelSerializer):
    job = JobBasicSerializer(read_only=True)
    applied_at = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Application
        fields = ['id', 'job', 'status', 'applied_at']
