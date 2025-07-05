from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

# local imports
from .serializers import JobSerializer, AppliedJobSerializer, ApplicationSerializer
from .models import Job, SavedJob, Application

class JobListAPIView(generics.ListAPIView):
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobSerializer

class JobDetailAPIView(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    lookup_field = 'id'

class SaveJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        job = Job.objects.get(id=id)
        SavedJob.objects.get_or_create(user=request.user, job=job)
        return Response({"message": "Job saved successfully."}, status=201)

    def delete(self, request, id):
        SavedJob.objects.filter(user=request.user, job_id=id).delete()
        return Response({"message": "Job unsaved successfully."}, status=204)

class IsSavedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        is_saved = SavedJob.objects.filter(user=request.user, job_id=id).exists()
        return Response({"saved": is_saved})

class ApplyToJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        job = get_object_or_404(Job, id=id)
        profile = request.user.profile

        if profile.role != 'jobseeker':
            return Response({"message": "Only jobseekers can apply."}, status=403)

        application, created = Application.objects.get_or_create(applicant=profile, job=job)

        if created:
            return Response({"message": "Applied successfully."}, status=201)

        return Response({"message": "Already applied."}, status=400)
    
class AppliedJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        applications = Application.objects.filter(applicant=request.user.profile).select_related('job')
        serializer = AppliedJobSerializer(applications, many=True)
        return Response(serializer.data)

class SavedJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved = SavedJob.objects.filter(user=request.user).select_related('job')
        jobs = [entry.job for entry in saved]
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

class CreateJobAPIView(generics.CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated] 
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class RecruiterJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

class RecruiterApplicantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recruiter_jobs = Job.objects.filter(created_by=request.user)
        applications = Application.objects.filter(job__in=recruiter_jobs).select_related('applicant__user', 'job')
        serializer = ApplicationSerializer(applications, many=True, context={'request': request})
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def applicant_detail(request, pk):
    try:
        application = Application.objects.select_related('applicant__user', 'job').get(pk=pk)
        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=200)
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application_status(request, pk):
    try:
        application = Application.objects.get(pk=pk)
        new_status = request.data.get('status')

        if new_status not in ['Pending', 'Approved', 'Rejected']:
            return Response({'error': 'Invalid status value'}, status=400)

        application.status = new_status
        application.save()

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=200)

    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)



