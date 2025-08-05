from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from jobs.models import Job, Application, SavedJob
from jobs.serializers.jobseeker_serializers import AppliedJobSerializer
from jobs.serializers.common_serializers import JobBasicSerializer


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


class SaveJobView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        job = get_object_or_404(Job, id=id)
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
        return Response({"saved": is_saved})

    def post(self, request, id):
        job = get_object_or_404(Job, id=id)
        SavedJob.objects.get_or_create(user=request.user, job=job)
        return Response({"message": "Job saved successfully."}, status=201)

    def delete(self, request, id):
        SavedJob.objects.filter(user=request.user, job_id=id).delete()
        return Response({"message": "Job unsaved successfully."}, status=204)


class SavedJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved = SavedJob.objects.filter(user=request.user).select_related('job')
        jobs = [entry.job for entry in saved]
        serializer = JobBasicSerializer(jobs, many=True)
        return Response(serializer.data)

