from django.urls import path
from rest_framework.routers import DefaultRouter
from jobs.views.recruiter_views import (
    RecruiterJobViewSet,
    JobApplicantsView,
    applicant_detail,
    update_application_status,
    CompanyAPIView,
)

router = DefaultRouter()
router.register(r'recruiter/jobs', RecruiterJobViewSet, basename='recruiter-jobs')

urlpatterns = [
    path('recruiter/jobs/<int:job_id>/applicants/', JobApplicantsView.as_view(), name='job-applicants'),
    path('recruiter/applicants/<int:pk>/', applicant_detail, name='applicant-detail'),
    path('recruiter/applicants/<int:pk>/status/', update_application_status, name='application-status'),
    path("recruiter/company/", CompanyAPIView.as_view(), name="company-profile"),

]

urlpatterns += router.urls
