from rest_framework.test import APITestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from unittest.mock import patch

RESET_TOKEN_SALT = "password-reset"
RESET_TOKEN_MAX_AGE_SECONDS = 15 * 60 
DAILY_RESEND_LIMIT = 5

from django.core.cache import cache
import time
from django.utils import timezone
from datetime import timedelta
from django.core import signing
from accounts.utils import generate_otp, hash_otp

class ForgotPasswordViewTest(APITestCase):

    def setUp(self):
        self.url = reverse("forgot-password")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Test@1234"
        )

    def test_forgot_password_existing_user(self):
        response = self.client.post(self.url, {"email": "test@example.com"})

        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        self.assertIsNotNone(profile.otp_hash)

    @patch("accounts.views.send_otp_email")
    def test_forgot_password_non_existing_user(self, mock_send):
        response = self.client.post(self.url, {"email": "ghost@example.com"})

        self.assertEqual(response.status_code, 200)
        mock_send.assert_not_called()

    def test_forgot_password_resend_rate_limited(self):
        profile = Profile.objects.get(user=self.user)
        profile.otp_resend_count = DAILY_RESEND_LIMIT
        profile.last_otp_sent_at = timezone.now()
        profile.save()

        response = self.client.post(self.url, {"email": "test@example.com"})

        self.assertEqual(response.status_code, 429)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class VerifyForgotOtpViewTest(APITestCase):

    def setUp(self):
        cache.clear()
        self.url = reverse("verify-forgot-otp")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Test@1234"
        )
        self.profile = Profile.objects.get(user=self.user)

        self.otp = generate_otp()
        self.profile.otp_hash = hash_otp(self.otp)
        self.profile.otp_created_at = timezone.now()
        self.profile.save()


    def test_verify_valid_otp(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": self.otp
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("reset_token", response.data)

    def test_verify_invalid_otp(self):
        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": "000000"
        })

        self.assertEqual(response.status_code, 400)

    def test_expired_otp(self):
        self.profile.otp_created_at = timezone.now() - timedelta(minutes=20)
        self.profile.save()

        response = self.client.post(self.url, {
            "email": "test@example.com",
            "otp": self.otp
        })

        self.assertEqual(response.status_code, 400)
    
    def test_otp_invalidated_after_success(self):
        self.client.post(self.url, {
            "email": "test@example.com",
            "otp": self.otp
        })

        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.otp_hash)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class ResetPasswordViewTest(APITestCase):

    def setUp(self):
        cache.clear()
        self.url = reverse("reset-password")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPass@123"
        )

        self.reset_token = signing.dumps(
            {"email": "test@example.com"},
            salt=RESET_TOKEN_SALT
        )

    def test_reset_password_success(self):
        response = self.client.post(self.url, {
            "reset_token": self.reset_token,
            "password": "NewStrongPass@123",
            "confirm_password":"NewStrongPass@123",
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass@123"))

    def test_reset_password_invalid_token(self):
        response = self.client.post(self.url, {
            "reset_token": "invalid-token",
            "password": "NewStrongPass@123",
            "confirm_password":"NewStrongPass@123",
        })

        self.assertEqual(response.status_code, 400)
    
    def test_reset_password_expired_token(self):
        reset_token = signing.dumps(
            {"email": "test@example.com"},
            salt=RESET_TOKEN_SALT
        )

        base_time = time.time()

        with patch("django.core.signing.time.time") as mock_time:
            mock_time.return_value = base_time + RESET_TOKEN_MAX_AGE_SECONDS + 1

            response = self.client.post(self.url, {
                "reset_token": reset_token,
                "password": "NewStrongPass@123",
                "confirm_password": "NewStrongPass@123",
            })

        self.assertEqual(response.status_code, 400)


# from rest_framework_simplejwt.tokens import RefreshToken

# class LogoutViewTest(APITestCase):

#     def setUp(self):
#         self.url = reverse("logout")
#         self.user = User.objects.create_user(
#             username="testuser",
#             email="test@example.com",
#             password="Test@1234"
#         )
#         self.refresh = RefreshToken.for_user(self.user)
#         self.client.credentials(
#             HTTP_AUTHORIZATION=f"Bearer {self.refresh.access_token}"
#         )

#     def test_logout_success(self):
#         response = self.client.post(self.url, {
#             "refresh_token": str(self.refresh)
#         })

#         self.assertEqual(response.status_code, 205)

#     def test_logout_invalid_token(self):
#         response = self.client.post(self.url, {
#             "refresh_token": "invalid"
#         })

#         self.assertEqual(response.status_code, 400)
