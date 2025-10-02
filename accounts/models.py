from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from cloudinary_storage.storage import MediaCloudinaryStorage 
from .storages import RawMediaCloudinaryStorage

class Profile(models.Model):
    ROLE_CHOICES = (
        ('jobseeker', 'Jobseeker'),
        ('recruiter', 'Recruiter'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)

    # OTP fields
    otp_hash = models.CharField(max_length=64, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.IntegerField(default=0)      
    last_otp_sent_at = models.DateTimeField(blank=True, null=True)
    otp_resend_count = models.IntegerField(default=0) 

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jobseeker')
    name = models.CharField(max_length=100)
    
    phone = models.CharField(max_length=15, blank=True)
    education = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    skills = models.JSONField(default=list)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True, storage=RawMediaCloudinaryStorage())
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True,storage=MediaCloudinaryStorage())

    def __str__(self):
        return self.name

class PendingUser(models.Model):
    ROLE_CHOICES = (
        ('jobseeker', 'Jobseeker'),
        ('recruiter', 'Recruiter'),
    )

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jobseeker')

    # OTP fields
    otp_hash = models.CharField(max_length=64, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.IntegerField(default=0)
    otp_resend_count = models.IntegerField(default=0)
    last_otp_sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def set_password(self, raw_password):
        """Hash the password like Django does for real User."""
        self.password = make_password(raw_password)
