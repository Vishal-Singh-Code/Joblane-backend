import django_filters
from django.db.models import Q
from .models import Job


class JobFilter(django_filters.FilterSet):
    profile = django_filters.CharFilter(method="filter_profile")
    location = django_filters.CharFilter(method="filter_location")

    job_type = django_filters.BaseInFilter(
        field_name="job_type", lookup_expr="in"
    )

    experience = django_filters.CharFilter(method="filter_experience")

    class Meta:
        model = Job
        fields = []

    def filter_profile(self, queryset, name, value):
        values = [v.strip() for v in value.split(",") if v.strip()]
        q = Q()
        for v in values:
            q |= Q(title__icontains=v)
        return queryset.filter(q)

    def filter_location(self, queryset, name, value):
        values = [v.strip() for v in value.split(",") if v.strip()]
        q = Q()
        for v in values:
            q |= Q(location__icontains=v)
        return queryset.filter(q)

    def filter_experience(self, queryset, name, value):
        if value == "Fresher":
            return queryset.filter(experience=0)
        if value == "Experienced":
            return queryset.filter(experience__gt=0)
        return queryset
