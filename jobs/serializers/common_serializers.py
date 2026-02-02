from rest_framework import serializers
from jobs.models import Job, Company

    
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "logo"]


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)
    applicants_count = serializers.IntegerField(read_only=True)
    is_saved = serializers.BooleanField(read_only=True)
    has_applied = serializers.BooleanField(read_only=True)

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'company']


class JobBasicSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)
    applicant_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'company_name', 'location', 'ctc', 'job_type','experience', 'company_logo', 'created_at', 'deadline', 'applicant_count']
        read_only_fields = ['created_at', 'deadline'] 

