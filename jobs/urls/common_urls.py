from django.urls import path
from jobs.views.common_views import JobListAPIView, JobDetailAPIView

urlpatterns = [
    path('jobs/', JobListAPIView.as_view(), name='job-list'),
    path('jobs/<int:id>/', JobDetailAPIView.as_view(), name='job-detail'),
]
