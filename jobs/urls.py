from django.urls import path
from . import views

urlpatterns = [
    # Job Views
    path('jobs/', views.JobListAPIView.as_view(), name='job-list'),
    path('jobs/<int:id>/', views.JobDetailAPIView.as_view(), name='job-detail'),
    path('jobs/<int:id>/save/', views.SaveJobView.as_view(), name='job-save'),
    path('jobs/<int:id>/is_saved/', views.IsSavedView.as_view(), name='job-is-saved'),
    path('jobs/<int:id>/apply/', views.ApplyToJobView.as_view(), name='job-apply'),
    path('jobs/applied/', views.AppliedJobsView.as_view(), name='applied-jobs'),
    path('jobs/saved/', views.SavedJobsView.as_view(), name='saved-jobs'),
    path('jobs/create/', views.CreateJobAPIView.as_view(), name='job-create'),

    # Recruiter Views
    path('jobs/recruiter/jobs', views.RecruiterJobsView.as_view(), name='recruiter-jobs'),
    path('recruiter/applicants/', views.RecruiterApplicantsView.as_view(), name='recruiter-applicants'),

    # Application Detail & Status
    path('applicants/<int:pk>/', views.applicant_detail, name='applicant-detail'),
    path('applications/<int:pk>/status/', views.update_application_status, name='application-status-update'),
]
