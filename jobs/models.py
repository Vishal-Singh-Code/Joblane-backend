from django.db import models
from accounts.models import Profile
from django.contrib.auth import get_user_model
from cloudinary_storage.storage import MediaCloudinaryStorage 

User = get_user_model()

class Company(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    logo = models.ImageField(
        upload_to="company_logos/",
        storage=MediaCloudinaryStorage(),
        null=True,
        blank=True
    )
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="company"
    )

    def __str__(self):
        return self.name


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'Full-time', 'Full-time'
        INTERNSHIP = 'Internship', 'Internship'
        PART_TIME = 'Part-time', 'Part-time'
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'


    title = models.CharField(max_length=255, db_index=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=False,   
        blank=False  
    )
    location = models.CharField(max_length=100, db_index=True)
    ctc = models.CharField(max_length=50)
    experience = models.CharField(max_length=100)
    deadline = models.DateField(db_index=True)

    job_type = models.CharField(max_length=20, choices=JobType.choices)

    description = models.TextField()

    responsibilities = models.JSONField(default=list, blank=True)
    requirements = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list,blank=True)
    perks = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs', db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs', db_index=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by', db_index=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'job'],
                name='unique_saved_job'
            )
        ]


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        SHORTLISTED = 'Shortlisted', 'Shortlisted'
        REJECTED = 'Rejected', 'Rejected'

    applicant = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='applications', db_index=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications', db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['applicant', 'job'],
                name='unique_job_application'
            )
        ]
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.name} applied for {self.job.title}"
