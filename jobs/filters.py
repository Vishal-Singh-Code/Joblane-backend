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
        fresher_query = (
            Q(experience__iexact="0")
            | Q(experience__iexact="0 years")
            | Q(experience__iexact="0 year")
            | Q(experience__iexact="fresher")
            | Q(experience__regex=r"^0\s*[-to]")
            | Q(experience__istartswith="0+")
        )

        if value == "Fresher":
            return queryset.filter(fresher_query)
        if value == "Experienced":
            return queryset.exclude(fresher_query)
        return queryset
