from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch

from accounts.models import PendingUser

@patch("accounts.views.send_otp_email")
class RegisterViewTest(APITestCase):

    def setUp(self):
        cache.clear()
        PendingUser.objects.all().delete()
        self.url = reverse("register")

    def test_successful_registration(self, mock_send_otp):
        mock_send_otp.return_value = (True, "OTP sent")

        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "name": "Test User",
            "role": "jobseeker",
            "password": "StrongPass123",
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PendingUser.objects.filter(email="test@example.com").exists())
        mock_send_otp.assert_called_once()

    def test_reregistration_updates_existing_pending_user(self, mock_send_otp):
        mock_send_otp.return_value = (True, "OTP sent")

        PendingUser.objects.create(email="test@example.com", username="oldname")

        payload = {
            "email": "test@example.com",
            "username": "newname",
            "name": "New Name",
            "role": "jobseeker",
            "password": "NewStrongPass123",
        }

        self.client.post(self.url, payload)

        user = PendingUser.objects.get(email="test@example.com")
        self.assertEqual(user.username, "newname")

    def test_password_is_hashed(self, mock_send_otp):
        mock_send_otp.return_value = (True, "OTP sent")

        payload = {
            "email": "secure@example.com",
            "username": "secureuser",
            "name": "Secure User",
            "role": "jobseeker",
            "password": "PlainPassword123",
        }

        self.client.post(self.url, payload)

        user = PendingUser.objects.get(email="secure@example.com")
        self.assertNotEqual(user.password, "PlainPassword123")

    def test_registration_throttling(self, mock_send_otp):
        mock_send_otp.return_value = (True, "OTP sent")

        payload = {
            "email": "throttle@example.com",
            "username": "throttleuser",
            "name": "Throttle User",
            "role": "jobseeker",
            "password": "StrongPass123",
        }

        for _ in range(3):
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
