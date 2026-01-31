from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

from django.contrib.auth import get_user_model
from accounts.models import PendingUser
from accounts.utils import hash_otp, OTP_EXPIRY_MINUTES

User = get_user_model()


class VerifyOtpViewTest(APITestCase):

    def setUp(self):
        cache.clear()
        PendingUser.objects.all().delete()
        User.objects.all().delete()

        self.url = reverse("verify-otp")

        self.pending_user = PendingUser.objects.create(
            email="test@example.com",
            username="testuser",
            name="Test User",
            role="jobseeker",
            password="StrongPass123",
            otp_hash=hash_otp("123456"),
            otp_created_at=timezone.now(),
            otp_attempts=0,
        )

    def test_verify_otp_success(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": "123456",
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())
        self.assertFalse(PendingUser.objects.filter(email="test@example.com").exists())

    def test_invalid_otp_increments_attempts(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": "000000",
        })

        self.pending_user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.pending_user.otp_attempts, 1)

    def test_otp_expired(self):
        self.pending_user.otp_created_at = timezone.now() - timedelta(
            minutes=OTP_EXPIRY_MINUTES + 1
        )
        self.pending_user.save()

        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": "123456",
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_many_attempts_blocked(self):
        self.pending_user.otp_attempts = 5
        self.pending_user.save()

        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": "123456",
        })

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_invalid_email(self):
        response = self.client.post(self.url, {
            "email": "wrong@example.com",
            "otp": "123456",
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
