"""Wordle models."""

from dataclasses import dataclass
from enum import StrEnum

from django.contrib.auth.models import User
from django.db import models


class TermTheme(models.TextChoices):
    """Word themes."""

    PHILOSOPHY = "ph", "Philosophy"
    HISTORY = "hi", "History"
    PHILOLOGY = "phl", "Philology"
    ART = "ar", "Art"
    SOCIETY = "so", "Society"


@dataclass(frozen=True)
class TermFilter:
    """Term filter."""

    theme: TermTheme
    length: int

    def get_hash(self) -> str:
        """Get hash."""
        return f"{self.theme}-{self.length}"


class LetterStatus(StrEnum):
    """Letter status in Wordle game."""

    GREEN = "green"
    YELLOW = "yellow"
    GRAY = "gray"


class Term(models.Model):
    """Wordle term."""

    word = models.CharField(max_length=16, unique=True)
    theme = models.CharField(max_length=14, choices=TermTheme.choices)
    length = models.PositiveIntegerField()
    definition = models.TextField()

    def __str__(self) -> str:
        """Return word."""
        return self.word


class AllowedWord(models.Model):
    """Word that user is allowed to enter."""

    word = models.CharField(max_length=16, unique=True)
    length = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        self.word = self.word.lower().strip()
        self.length = len(self.word)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.word


class Game(models.Model):
    """Wordle game."""
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    attempts = models.IntegerField(default=0)
    is_won = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    max_attempts = models.IntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return word."""
        return self.term.word


class Profile(models.Model):
    """Wordle profile."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    random_seed = models.PositiveIntegerField()
    term_indexes = models.JSONField(default=dict)

    def __str__(self) -> str:
        """Return username."""
        return self.user.username
