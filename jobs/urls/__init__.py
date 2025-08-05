from django.urls import path, include

urlpatterns = [
    path('', include('jobs.urls.common_urls')),
    path('', include('jobs.urls.jobseeker_urls')),
    path('', include('jobs.urls.recruiter_urls')),
]
