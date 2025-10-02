from django.urls import path
from jobs.views.jobseeker_views import (
    ApplyToJobView,
    AppliedJobsView,
    SaveJobView,
    SavedJobsView,
    get_filter_options
)

urlpatterns = [
    path('jobs/<int:id>/apply/', ApplyToJobView.as_view(), name='apply-job'),
    path('applied/', AppliedJobsView.as_view(), name='applied-jobs'),
    
    path('jobs/<int:id>/save/', SaveJobView.as_view(), name='save-job'),
    path('saved/', SavedJobsView.as_view(), name='saved-jobs'),
    path('filters/', get_filter_options, name="filter_options"),
]
