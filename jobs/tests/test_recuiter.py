from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils.timezone import localdate, timedelta
from jobs.models import Job, Application
from jobs.tests.utils import create_user, create_recruiter_with_company

class RecruiterFlowTest(APITestCase):

    def setUp(self):
        self.recruiter = create_recruiter_with_company()
        self.jobseeker = create_user("candidate@test.com", "jobseeker")

        self.job = Job.objects.create(
            title="Python Dev",
            company=self.recruiter.company,
            location="Remote",
            ctc="12 LPA",
            experience="2 years",
            deadline=localdate() + timedelta(days=10),
            job_type="Full-time",
            description="Test",
            created_by=self.recruiter
        )

        self.application = Application.objects.create(
            applicant=self.jobseeker.profile,
            job=self.job
        )

        self.client.force_authenticate(self.recruiter)

    def test_list_applicants(self):
        url = reverse("job-applicants", args=[self.job.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_update_application_status(self):
        url = reverse("application-status", args=[self.application.id])
        response = self.client.patch(
            url,
            {"status": "Shortlisted"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Shortlisted")

    def test_recruiter_cannot_access_other_jobs(self):
        other_recruiter = create_recruiter_with_company()
        self.client.force_authenticate(other_recruiter)

        url = reverse("job-applicants", args=[self.job.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
