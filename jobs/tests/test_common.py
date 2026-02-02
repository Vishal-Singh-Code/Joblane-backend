from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils.timezone import localdate, timedelta
from jobs.models import Job
from jobs.tests.utils import create_recruiter_with_company

class JobCommonViewsTest(APITestCase):

    def setUp(self):
        self.recruiter = create_recruiter_with_company()
        self.job = Job.objects.create(
            title="Backend Engineer",
            company=self.recruiter.company,
            location="Remote",
            ctc="10 LPA",
            experience="1-3 years",
            deadline=localdate() + timedelta(days=5),
            job_type="Full-time",
            description="Test job",
            created_by=self.recruiter
        )

    def test_job_list(self):
        url = reverse("job-list")  # match your URL name
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_job_detail_requires_auth(self):
        url = reverse("job-detail", args=[self.job.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)
