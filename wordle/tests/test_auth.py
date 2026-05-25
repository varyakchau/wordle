from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from wordle.models import Profile


class AuthAPITestCase(APITestCase):
    def test_register_creates_user_and_profile(self) -> None:
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "korney",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "Пользователь создан"})

        user = User.objects.get(username="korney")

        self.assertTrue(user.check_password("password123"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_without_username_returns_400(self) -> None:
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"error": "Нужно ввести username и password"},
        )

    def test_register_without_password_returns_400(self) -> None:
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "korney",
                "password": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"error": "Нужно ввести username и password"},
        )

    def test_register_existing_user_returns_400(self) -> None:
        User.objects.create_user(username="korney", password="password123")

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "korney",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Такой пользователь уже есть"})

    def test_login_with_correct_password_returns_200(self) -> None:
        User.objects.create_user(username="korney", password="password123")

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "korney",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Пользователь авторизован"})

    def test_login_with_wrong_password_returns_401(self) -> None:
        User.objects.create_user(username="korney", password="password123")

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "korney",
                "password": "wrong-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data,
            {"error": "Неверное имя пользователя или пароль"},
        )

    def test_login_with_unknown_user_returns_401(self) -> None:
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "unknown",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data,
            {"error": "Неверное имя пользователя или пароль"},
        )
