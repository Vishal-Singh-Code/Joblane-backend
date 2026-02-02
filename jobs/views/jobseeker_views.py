from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils.timezone import localdate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics,status

# local imports
from jobs.models import Job, Application, SavedJob
from jobs.serializers.jobseeker_serializers import AppliedJobSerializer
from jobs.serializers.common_serializers import JobBasicSerializer
from jobs.permissions import IsJobSeeker
from jobs.pagination import StandardPagination



class ApplyToJobView(APIView):
    permission_classes = [IsAuthenticated, IsJobSeeker]

    def post(self, request, id):
        job = get_object_or_404(Job.objects.only('id', 'deadline'), id=id)

        profile = request.user.profile

        if job.deadline < localdate():
            return Response({"message": "This job has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if not profile.resume:
            return Response({"message": "Please upload your resume before applying."}, status=status.HTTP_400_BAD_REQUEST)

        _, created = Application.objects.get_or_create(applicant=profile, job=job)

        if created:
            return Response({"message": "Applied successfully."}, status=status.HTTP_201_CREATED)

        return Response({"message": "Already applied."}, status=status.HTTP_409_CONFLICT)


class AppliedJobsView(generics.ListAPIView):
    serializer_class = AppliedJobSerializer
    permission_classes = [IsAuthenticated, IsJobSeeker]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (Application.objects.filter(applicant=self.request.user.profile).select_related('job'))


class SaveJobView(APIView):
    permission_classes = [IsAuthenticated,IsJobSeeker]

    def get(self, request, id):
        job = get_object_or_404(Job.objects.only('id', 'deadline'), id=id)
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
        return Response({"saved": is_saved})

    def post(self, request, id):
        job = get_object_or_404(Job.objects.only('id', 'deadline'), id=id)

        if job.deadline < localdate() :
            return Response({"message": "This job has expired and cannot be saved."}, status=400)
        
        _, created = SavedJob.objects.get_or_create(user=request.user, job=job)

        if created:
            return Response({"message": "Job saved successfully."}, status=201)
        
        return Response({"message": "Already Saved."}, status=status.HTTP_409_CONFLICT)



    def delete(self, request, id):
        deleted, _ = SavedJob.objects.filter(user=request.user,job_id=id).delete()

        if deleted == 0:
            return Response(
                {"message": "Job was not saved."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedJobsView(generics.ListAPIView):
    serializer_class = JobBasicSerializer
    permission_classes = [IsAuthenticated, IsJobSeeker]
    pagination_class = StandardPagination


    def get_queryset(self):
        return (
            Job.objects
            .filter(saved_by__user=self.request.user, deadline__gte=localdate())
            .select_related('company')
            .annotate(applicant_count=Count('applications', distinct=True))
            .order_by('-created_at')
        )


class JobFilterOptionsView(APIView):

    def get(self, request):
        active_jobs = Job.objects.filter(deadline__gte=localdate())

        return Response({
            "locations": sorted(active_jobs.values_list('location', flat=True).distinct()),
            "profiles": sorted(active_jobs.values_list('title', flat=True).distinct()),
        })
