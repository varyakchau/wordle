from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from wordle.models import Profile, Term


class DefinitionAPITestCase(APITestCase):
    def test_definition_returns_term_definition(self) -> None:
        user = User.objects.create_user(
            username="korney",
            password="password123",
        )
        Profile.objects.create(
            user=user,
            random_seed=123,
            term_indexes={},
        )

        Term.objects.create(
            word="логос",
            theme="ph",
            length=5,
            definition="Философский термин.",
        )

        self.client.force_authenticate(user=user)
        response = self.client.get("/api/definition/", {"word": "логос"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "word": "логос",
                "theme": "ph",
                "definition": "Философский термин.",
            },
        )
