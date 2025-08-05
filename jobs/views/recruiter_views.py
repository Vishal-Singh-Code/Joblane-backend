from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework import status



from jobs.models import Job, Application
from jobs.serializers.recruiter_serializers import ApplicationSerializer, BasicApplicationSerializer
from jobs.serializers.common_serializers import JobSerializer, JobBasicSerializer



# class CreateJobAPIView(generics.CreateAPIView):
#     queryset = Job.objects.all()
#     serializer_class = JobSerializer
#     permission_classes = [IsAuthenticated] 
#     def perform_create(self, serializer):
#         if self.request.user.profile.role != 'recruiter':
#             raise PermissionDenied("Only recruiters can create jobs.")
#         serializer.save(created_by=self.request.user)

# class RecruiterJobsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')
#         serializer = JobSerializer(jobs, many=True)
#         return Response(serializer.data)

class RecruiterJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JobBasicSerializer
        return JobSerializer

    def perform_create(self, serializer):
        if self.request.user.profile.role != 'recruiter':
            raise PermissionDenied("Only recruiters can create jobs.")
        serializer.save(created_by=self.request.user)

# class RecruiterApplicantsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         recruiter_jobs = Job.objects.filter(created_by=request.user)
#         applications = Application.objects.filter(job__in=recruiter_jobs).select_related('applicant__user', 'job')
#         serializer = ApplicationSerializer(applications, many=True, context={'request': request})
#         return Response(serializer.data)

class JobApplicantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)

        if job.created_by != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        applications = Application.objects.filter(job=job).select_related('applicant__user')
        serializer = BasicApplicationSerializer(applications, many=True, context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def applicant_detail(request, pk):
    try:
        application = Application.objects.select_related('job__created_by', 'applicant__user').get(pk=pk)
        if application.job.created_by != request.user:
            return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=200)
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application_status(request, pk):
    try:
        application = Application.objects.select_related('job__created_by').get(pk=pk)
        if application.job.created_by != request.user:
            return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')

        if new_status not in ['Pending', 'Approved', 'Rejected']:
            return Response({'error': 'Invalid status value'}, status=400)

        application.status = new_status
        application.save()

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=200)

    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)
