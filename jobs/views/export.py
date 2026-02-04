from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
import openpyxl
from django.utils.timezone import localtime
from jobs.models import Application

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_applicants(request):
    job_id = request.GET.get("job_id")
    status = request.GET.get("status")

    qs = Application.objects.select_related("applicant", "job")

    if job_id:
        qs = qs.filter(job_id=job_id)

    if status and status.lower() != "all":
        qs = qs.filter(status=status)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Applicants"

    ws.append([
        "Applicant Name",
        "Email",
        "Phone",
        "Job Title",
        "Status",
        "Applied On",
    ])

    for app in qs:
        ws.append([
            app.applicant.name,
            app.applicant.user.email,
            app.applicant.phone,
            app.job.title,
            app.status,
            localtime(app.applied_at).strftime("%d %b %Y"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="applicants.xlsx"'
    wb.save(response)
    return response
