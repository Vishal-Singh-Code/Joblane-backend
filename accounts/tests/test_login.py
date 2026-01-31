from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache

from django.contrib.auth import get_user_model

User = get_user_model()


class LoginViewTest(APITestCase):

    def setUp(self):
        cache.clear()
        User.objects.all().delete()

        # IMPORTANT: use create_user (hashes password)
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123",
            is_active=True,
        )

        # Adjust this name if your URL is different
        self.url = reverse("login")

    # ✅ LOGIN WITH USERNAME
    def test_login_with_username_success(self):
        payload = {
            "username": "testuser",
            "password": "StrongPass123",
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["email"], "test@example.com")


    # ✅ LOGIN WITH EMAIL
    def test_login_with_email_success(self):
        payload = {
            "username": "test@example.com",
            "password": "StrongPass123",
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["email"], "test@example.com")


    # ❌ WRONG PASSWORD
    def test_login_wrong_password(self):
        payload = {
            "username": "testuser",
            "password": "WrongPassword123",
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ❌ NON-EXISTENT USER
    def test_login_invalid_user(self):
        payload = {
            "username": "nouser@example.com",
            "password": "StrongPass123",
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ❌ INACTIVE USER (VERY IMPORTANT)
    def test_login_inactive_user_blocked(self):
        self.user.is_active = False
        self.user.save()

        payload = {
            "username": "testuser",
            "password": "StrongPass123",
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
