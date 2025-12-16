from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Profile
from cloudinary_storage.storage import MediaCloudinaryStorage 

User = get_user_model()

class Company(models.Model):
    name = models.CharField(max_length=255)
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
    JOB_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Internship', 'Internship'),
        ('Part-time', 'Part-time'),
        ('Remote', 'Remote'),
        ('Hybrid', 'Hybrid')
    ]

    title = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=False,   
        blank=False  
    )
    location = models.CharField(max_length=100)
    ctc = models.CharField(max_length=50)
    experience = models.CharField(max_length=100)
    deadline = models.DateField()

    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)

    description = models.TextField()

    responsibilities = models.JSONField(default=list)
    requirements = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    perks = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')

    def __str__(self):
        return f"{self.title} at {self.company}"

class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

class Application(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
    )
    applicant = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    class Meta: 
        unique_together = ('applicant', 'job')

    def __str__(self):
        return f"{self.applicant.name} applied for {self.job.title}"
