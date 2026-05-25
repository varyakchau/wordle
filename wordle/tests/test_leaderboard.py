from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from wordle.models import Profile


class LeaderboardAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="korney",
            password="password123",
        )
        Profile.objects.create(
            user=self.user,
            rating=10,
            random_seed=123,
            term_indexes={},
        )

        user_2 = User.objects.create_user(
            username="alice",
            password="password123",
        )
        Profile.objects.create(
            user=user_2,
            rating=30,
            random_seed=456,
            term_indexes={},
        )

    def test_leaderboard_requires_auth(self) -> None:
        response = self.client.get("/api/leaderboard/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"error": "Пользователь не авторизован"})

    def test_leaderboard_returns_profiles_ordered_by_rating(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/leaderboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["username"], "alice")
        self.assertEqual(response.data[0]["rating"], 30)
        self.assertEqual(response.data[1]["username"], "korney")
        self.assertEqual(response.data[1]["rating"], 10)
