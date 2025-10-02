from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.utils.timezone import now


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
        
        if job.deadline < now().date():
            return Response({"message": "This job has expired."}, status=400)
        
        if not profile.resume:
            return Response({"message": "Please upload your resume before applying."}, status=400)

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
        if job.deadline < now().date():
            return Response({"message": "This job has expired and cannot be saved."}, status=400)
        saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if created:
            return Response({"message": "Job saved successfully."}, status=201)
        return Response({"message": "Job already saved."}, status=400)


    def delete(self, request, id):
        SavedJob.objects.filter(user=request.user, job_id=id).delete()
        return Response({"message": "Job unsaved successfully."}, status=204)


class SavedJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.filter(savedjob__user=request.user, deadline__gte=now().date())
        serializer = JobBasicSerializer(jobs, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def get_filter_options(request):
    # Filter only active jobs
    active_jobs = Job.objects.filter(deadline__gte=now())

    # Get distinct locations and job titles
    locations = active_jobs.values_list('location', flat=True).distinct()
    profiles = active_jobs.values_list('title', flat=True).distinct()

    return Response({
        "locations": sorted(locations),
        "profiles": sorted(profiles),
    })