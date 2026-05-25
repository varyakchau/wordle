"""Wordle utils."""

from dataclasses import dataclass

from .models import LetterStatus


@dataclass(frozen=True)
class LetterWithStatus:
    """Letter with status."""

    letter: str
    status: LetterStatus


def normalize_word(word: str) -> str:
    """Normalize word."""
    return word.lower().replace("ё", "е")


def compare_words(guess: str, answer: str) -> list[LetterWithStatus]:
    """Compare words."""
    guess = normalize_word(guess)
    answer = normalize_word(answer)

    result = []

    for i in range(len(guess)):
        letter = guess[i]

        if guess[i] == answer[i]:
            status = LetterStatus.GREEN
        elif letter in answer:
            status = LetterStatus.YELLOW
        else:
            status = LetterStatus.GRAY

        letter_with_status = LetterWithStatus(letter, status)
        result.append(letter_with_status)

    return result
