from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from wordle.models import Game, Profile, Term


class GameAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="korney",
            password="password123",
        )
        self.profile = Profile.objects.create(
            user=self.user,
            random_seed=123,
            term_indexes={},
        )

        self.term = Term.objects.create(
            word="логос",
            theme="ph",
            length=5,
            definition="Философский термин.",
        )

    def test_start_game_requires_auth(self) -> None:
        response = self.client.post(
            "/api/start-game/",
            {
                "theme": "ph",
                "length": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"error": "Пользователь не авторизован"})

    def test_start_game_creates_game(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/start-game/",
            {
                "theme": "ph",
                "length": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("game_id", response.data)

        self.assertTrue(Game.objects.filter(user=self.user).exists())

        self.profile.refresh_from_db()
        self.assertEqual(len(self.profile.term_indexes), 1)

    def test_start_game_without_theme_returns_400(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/start-game/",
            {
                "length": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Нужно выбрать тему"})

    def test_start_game_without_length_returns_400(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/start-game/",
            {
                "theme": "ph",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Нужно выбрать длину слова"})

    def test_start_game_without_terms_returns_404(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/start-game/",
            {
                "theme": "hi",
                "length": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data,
            {"error": "Новых слов с такими параметрами больше нет"},
        )

    def test_make_guess_requires_auth(self) -> None:
        game = Game.objects.create(user=self.user, term=self.term)

        response = self.client.post(
            "/api/make-guess/",
            {
                "game_id": game.id,
                "word": "логос",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"error": "Пользователь не авторизован"})

    def test_make_guess_with_correct_word_finishes_game(self) -> None:
        self.client.force_authenticate(user=self.user)

        game = Game.objects.create(user=self.user, term=self.term)

        response = self.client.post(
            "/api/make-guess/",
            {
                "game_id": game.id,
                "word": "логос",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["attempts"], 1)
        self.assertEqual(response.data["attempts_left"], 5)
        self.assertTrue(response.data["is_finished"])
        self.assertTrue(response.data["is_won"])
        self.assertIn("result", response.data)
        self.assertEqual(response.data["answer"], "логос")
        self.assertEqual(response.data["definition"], "Философский термин.")

        game.refresh_from_db()
        self.assertTrue(game.is_finished)
        self.assertTrue(game.is_won)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.rating, 10)

    def test_make_guess_with_unknown_game_returns_404(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/make-guess/",
            {
                "game_id": 999,
                "word": "логос",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Игра не найдена"})

    def test_make_guess_with_wrong_length_returns_400(self) -> None:
        self.client.force_authenticate(user=self.user)

        game = Game.objects.create(user=self.user, term=self.term)

        response = self.client.post(
            "/api/make-guess/",
            {
                "game_id": game.id,
                "word": "логика",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Слово должно быть такой же длины"})

    def test_make_guess_after_game_finished_returns_400(self) -> None:
        self.client.force_authenticate(user=self.user)

        game = Game.objects.create(
            user=self.user,
            term=self.term,
            is_finished=True,
            is_won=True,
        )

        response = self.client.post(
            "/api/make-guess/",
            {
                "game_id": game.id,
                "word": "логос",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Игра уже закончена"})
