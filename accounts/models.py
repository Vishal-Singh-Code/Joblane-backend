from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (
        ('jobseeker', 'Jobseeker'),
        ('recruiter', 'Recruiter'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)

    # Added fields
    phone = models.CharField(max_length=15, blank=True)
    education = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    skills = models.JSONField(default=list)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return self.name
