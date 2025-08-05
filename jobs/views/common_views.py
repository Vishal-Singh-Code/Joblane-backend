from rest_framework import generics
from django.utils.timezone import now


# local imports
from jobs.serializers.common_serializers import JobSerializer, JobBasicSerializer
from jobs.models import Job


class JobListAPIView(generics.ListAPIView):
    serializer_class = JobBasicSerializer
    def get_queryset(self):
        return Job.objects.filter(deadline__gte=now()).order_by('-created_at')

class JobDetailAPIView(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    lookup_field = 'id'
