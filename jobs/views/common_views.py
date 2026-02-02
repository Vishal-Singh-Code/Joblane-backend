from django.utils.timezone import localdate
from django.db import models
from django.db.models import Count, Exists, OuterRef
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from jobs.filters import JobFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter



# local imports
from jobs.serializers.common_serializers import JobSerializer, JobBasicSerializer
from jobs.models import Job, Application, SavedJob
from jobs.pagination import StandardPagination


class JobListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = JobBasicSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]  # 👈 REQUIRED

    filterset_class = JobFilter
    search_fields = ["title", "company__name", "location"]

    def get_queryset(self):
        return Job.objects.filter(deadline__gte=localdate()).select_related('company').annotate(applicant_count=Count('applications', distinct=True)).order_by('-created_at')


class JobDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user

        qs = (
            Job.objects
            .select_related('company', 'created_by')
            .annotate(
                applicants_count=Count('applications', distinct=True),
            )
        )

        if user.is_authenticated and hasattr(user, 'profile'):
            qs = qs.annotate(
                has_applied=Exists(
                    Application.objects.filter(
                        applicant=user.profile,
                        job=OuterRef('pk')
                    )
                ),
                is_saved=Exists(
                    SavedJob.objects.filter(
                        user=user,
                        job=OuterRef('pk')
                    )
                )
            )
        else:
            qs = qs.annotate(
                has_applied=models.Value(False, output_field=models.BooleanField()),
                is_saved=models.Value(False, output_field=models.BooleanField()),
            )

        return qs
