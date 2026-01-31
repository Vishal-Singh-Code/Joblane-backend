from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch

from accounts.models import PendingUser


class SendOtpViewTest(APITestCase):

    def setUp(self):
        cache.clear()
        PendingUser.objects.all().delete()
        self.url = reverse("send-otp")

        self.pending_user = PendingUser.objects.create(
            email="otp@example.com",
            username="otpuser",
            name="OTP User",
            role="jobseeker",
            password="StrongPass123",
        )

    @patch("accounts.views.send_otp_email")
    def test_send_otp_success(self, mock_send_otp):
        mock_send_otp.return_value = (True, "OTP sent successfully.")

        response = self.client.post(self.url, {"email": "otp@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_otp.assert_called_once()

    @patch("accounts.views.send_otp_email")
    def test_send_otp_blocked_by_rules(self, mock_send_otp):
        mock_send_otp.return_value = (False, "Daily OTP limit reached.")

        response = self.client.post(self.url, {"email": "otp@example.com"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_send_otp_invalid_email(self):
        response = self.client.post(self.url, {"email": "wrong@example.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
