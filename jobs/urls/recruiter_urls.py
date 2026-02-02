from django.urls import path
from rest_framework.routers import DefaultRouter
from jobs.views.recruiter_views import (
    RecruiterJobViewSet,
    JobApplicantsView,
    ApplicantDetailView,
    UpdateApplicationStatusView,
    CompanyAPIView,
)

router = DefaultRouter()
router.register(r'recruiter/jobs', RecruiterJobViewSet, basename='recruiter-jobs')

urlpatterns = [
    path('recruiter/jobs/<int:job_id>/applicants/', JobApplicantsView.as_view(), name='job-applicants'),
    path('recruiter/applicants/<int:pk>/', ApplicantDetailView.as_view(), name='applicant-detail'),
    path('recruiter/applicants/<int:pk>/status/', UpdateApplicationStatusView.as_view(), name='application-status'),
    path("recruiter/company/", CompanyAPIView.as_view(), name="company-profile"),

]

urlpatterns += router.urls
