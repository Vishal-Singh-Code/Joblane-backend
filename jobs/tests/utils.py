from django.contrib.auth import get_user_model
from accounts.models import Profile
from jobs.models import Company

User = get_user_model()

import uuid

def create_user(email, role):
    user = User.objects.create_user(
        username=f"{email}-{uuid.uuid4()}",
        email=email,
        password="testpass123"
    )

    profile = user.profile
    profile.role = role
    profile.save()

    return user



def create_recruiter_with_company():
    user = create_user("recruiter@test.com", "recruiter")
    Company.objects.create(
        owner=user,
        name="Test Company"
    )
    return user
