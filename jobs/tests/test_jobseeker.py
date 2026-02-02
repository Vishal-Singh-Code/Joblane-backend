from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils.timezone import localdate, timedelta
from jobs.models import Job, SavedJob, Application
from jobs.tests.utils import create_user, create_recruiter_with_company

class JobSeekerFlowTest(APITestCase):

    def setUp(self):
        self.jobseeker = create_user("jobseeker@test.com", "jobseeker")
        self.jobseeker.profile.resume = "dummy_resume.pdf"
        self.jobseeker.profile.save()
        self.recruiter = create_recruiter_with_company()

        self.job = Job.objects.create(
            title="Django Developer",
            company=self.recruiter.company,
            location="Bangalore",
            ctc="8 LPA",
            experience="1 year",
            deadline=localdate() + timedelta(days=5),
            job_type="Full-time",
            description="Test",
            created_by=self.recruiter
        )

        self.client.force_authenticate(self.jobseeker)

    def test_apply_to_job(self):
        url = reverse("apply-job", args=[self.job.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Application.objects.filter(
                applicant=self.jobseeker.profile,
                job=self.job
            ).exists()
        )

    def test_cannot_apply_twice(self):
        Application.objects.create(
            applicant=self.jobseeker.profile,
            job=self.job
        )

        url = reverse("apply-job", args=[self.job.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 409)

    def test_save_job(self):
        url = reverse("save-job", args=[self.job.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            SavedJob.objects.filter(
                user=self.jobseeker,
                job=self.job
            ).exists()
        )

    def test_view_saved_jobs(self):
        SavedJob.objects.create(
            user=self.jobseeker,
            job=self.job
        )

        url = reverse("saved-jobs")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
