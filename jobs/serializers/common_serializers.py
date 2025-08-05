from rest_framework import serializers
from jobs.models import Job, SavedJob, Application


class JobSerializer(serializers.ModelSerializer):
    applicants_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_applicants_count(self, obj):
        return Application.objects.filter(job=obj).count()

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedJob.objects.filter(user=request.user, job=obj).exists()
        return False

    def get_has_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'profile'):
            return Application.objects.filter(applicant=request.user.profile, job=obj).exists()
        return False

class JobBasicSerializer(serializers.ModelSerializer):
    applicant_count = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = ['id', 'title', 'company', 'location', 'ctc', 'job_type', 'logo_url', 'created_at','deadline', 'applicant_count']
        read_only_fields = ['created_at', 'deadline'] 
    def get_applicant_count(self, obj):
        return Application.objects.filter(job=obj).count()
