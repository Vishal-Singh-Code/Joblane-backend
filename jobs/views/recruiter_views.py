from django.shortcuts import get_object_or_404

from rest_framework import generics, viewsets,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied

# local import
from jobs.models import Job, Application, Company
from jobs.serializers.recruiter_serializers import ApplicationSerializer, BasicApplicationSerializer
from jobs.serializers.common_serializers import JobSerializer, JobBasicSerializer, CompanySerializer
from jobs.permissions import IsRecruiter, IsJobOwner
from jobs.pagination import StandardPagination



class RecruiterJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsRecruiter]

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user).select_related("company").order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JobBasicSerializer
        return JobSerializer

    def perform_create(self, serializer):
        user = self.request.user
        
        if not hasattr(user, "company"):
            raise PermissionDenied("Create company profile before posting jobs.")

        serializer.save(created_by=user, company=user.company)


class JobApplicantsView(generics.ListAPIView):
    serializer_class = BasicApplicationSerializer
    permission_classes = [IsAuthenticated, IsRecruiter, IsJobOwner]
    pagination_class = StandardPagination

    def get_job(self):
        return get_object_or_404(Job, id=self.kwargs['job_id'])

    def get_queryset(self):
        job = self.get_job()
        self.check_object_permissions(self.request, job)
        return (Application.objects.filter(job=job).select_related('applicant__user'))


class ApplicantDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsRecruiter,IsJobOwner]
    queryset = Application.objects.select_related('job__created_by', 'applicant__user')


class UpdateApplicationStatusView(generics.UpdateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsRecruiter,IsJobOwner]
    queryset = Application.objects.select_related('job__created_by')

    def patch(self, request, *args, **kwargs):
        application = self.get_object()
        status_value = request.data.get("status")

        if status_value not in Application.Status.values:
            return Response({"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

        application.status = status_value
        application.save()

        return Response(self.get_serializer(application).data, status=status.HTTP_200_OK)


class CompanyAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsRecruiter]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        company, _ = Company.objects.get_or_create(owner=self.request.user)
        return company
