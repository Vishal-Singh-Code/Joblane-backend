from rest_framework import serializers
from .models import Job, Application
from accounts.serializers import ProfileSerializer


class JobSerializer(serializers.ModelSerializer):
    applicants_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_applicants_count(self, obj):
        return Application.objects.filter(job=obj).count()

class JobShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title']

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = ProfileSerializer(read_only=True)
    job = JobShortSerializer(read_only=True) 

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'applied_at','status']

class AppliedJobSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='job.id',read_only=True) 
    title = serializers.CharField(source='job.title')
    company = serializers.CharField(source='job.company')
    location = serializers.CharField(source='job.location')
    ctc = serializers.CharField(source='job.ctc')
    job_type = serializers.CharField(source='job.job_type')
    logo_url = serializers.CharField(source='job.logo_url', allow_null=True, required=False)

    status = serializers.CharField()
    applied_at = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Application
        fields = ['id', 'title', 'company', 'location', 'ctc', 'job_type', 'logo_url', 'status', 'applied_at']
