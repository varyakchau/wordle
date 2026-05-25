import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from wordle.models import AllowedWord, Term


class Command(BaseCommand):
    """Django management command to import terms and allowed words from JSON files."""

    help = "Import terms and allowed words"

    def handle(self, *_: Any, **__: Any) -> None:
        """Handle the command to import terms and allowed words."""
        with Path("wordle/data/terms.json").open(encoding="utf-8") as file:
            terms_json = json.load(file)

        with Path("wordle/data/AllowedWords.json").open(encoding="utf-8") as file:
            allowed_words_json = json.load(file)

        allowed_words_list = allowed_words_json.get("allowed_words", [])

        term_words = [item["word"] for item in terms_json]
        Term.objects.bulk_create(
            [
                Term(
                    word=item["word"],
                    theme=item["theme"],
                    definition=item["definition"],
                    length=len(item["word"]),
                )
                for item in terms_json
                if len(item["word"]) <= 8
            ],
            ignore_conflicts=True,
        )

        AllowedWord.objects.bulk_create(
            [
                AllowedWord(
                    word=word,
                    length=len(word),
                )
                for word in allowed_words_list + term_words
            ],
            ignore_conflicts=True,
        )

        log_text = f"{len(terms_json)} terms and {len(allowed_words_list)} allowed words imported."
        self.stdout.write(self.style.SUCCESS(log_text))
