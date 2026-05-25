"""Wordle views."""
from typing import cast

import random
import secrets
from datetime import timedelta
from dataclasses import asdict

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from config.settings import PROFILE_RANDOM_SEED_UPPER_BOUND

from .errors import EmptyFieldError, UserAlreadyExistsError
from .models import Game, Profile, Term, TermFilter
from .utils import compare_words, normalize_word
from wordle.models import AllowedWord


# странички

def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("menu")
    return render(request, "index.html")


def auth_page(request: HttpRequest) -> HttpResponse:
    get_token(request)
    if request.user.is_authenticated:
        return redirect("menu")
    return render(request, "auth.html")


def menu(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("index")
    return render(request, "menu.html")


def game(request: HttpRequest, word_length: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("index")
    return render(request, "game.html", {"word_length": word_length})


def rating(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("index")
    return render(request, "rating.html")

# проверка, есть ли пользователь

def check_register_data(username: str | None, password: str | None) -> None:
    """Check register data.

    Raises:
        EmptyFieldError: If username or password is empty.
        UserAlreadyExistsError: If user already exists.

    """
    if not username or not password:
        raise EmptyFieldError

    if User.objects.filter(username=username).exists():
        raise UserAlreadyExistsError


@api_view(["POST"])
def register(request: Request) -> Response:
    """Register user."""
    try:
        username: str | None = request.data.get("username")
        password: str | None = request.data.get("password")

        check_register_data(username, password)
        
        username = cast(str, username)
        user = User.objects.create_user(
            username=username,
            password=password,
        )

        user_seed = secrets.randbelow(PROFILE_RANDOM_SEED_UPPER_BOUND)
        Profile.objects.create(user=user, random_seed=user_seed)

        return Response({"message": "Пользователь создан"}, status=201)
    except EmptyFieldError:
        return Response({"error": "Нужно ввести username и password"}, status=400)
    except UserAlreadyExistsError:
        return Response({"error": "Такой пользователь уже есть"}, status=400)


@api_view(["POST"])
def login(request: Request) -> Response:
    """Login user."""
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response({"error": "Неверное имя пользователя или пароль"}, status=401)

    django_login(request, user)

    return Response({"message": "Пользователь авторизован"}, status=200)


@api_view(["POST"])
def start_game(request: Request) -> Response:
    """Start game."""
    user = request.user

    if not user.is_authenticated:
        return Response({"error": "Пользователь не авторизован"}, status=401)

    # удаляем старые игры чтобы не засрать базу
    Game.objects.filter(user=user, created_at__lt=timezone.now() - timedelta(hours=1)).delete()

    theme = request.data.get("theme")
    length = request.data.get("length")
    profile = Profile.objects.get(user=user)

    if not theme:
        return Response({"error": "Нужно выбрать тему"}, status=400)
    if not length:
        return Response({"error": "Нужно выбрать длину слова"}, status=400)

    terms = Term.objects.filter(theme=theme, length=length)
    if not terms.exists():
        return Response(
            {"error": "Новых слов с такими параметрами больше нет"},  # noqa: RUF001
            status=404,
        )

    term_hash = TermFilter(theme=theme, length=length).get_hash()
    terms_list = list(terms.order_by("id"))

    attempt: int = profile.term_indexes.get(term_hash, 0)
    random_seed: int = profile.random_seed

    rng = random.Random(random_seed)  # noqa: S311
    rng.shuffle(terms_list)

    if attempt >= len(terms_list):
        return Response(
            {"error": "Новых слов с такими параметрами больше нет"},  # noqa: RUF001
            status=404,
        )

    term = terms_list[attempt]

    game = Game.objects.create(
        user=user,
        term=term,
    )

    profile.term_indexes[term_hash] = attempt + 1
    profile.save(update_fields=["term_indexes"])

    return Response(
        {
            "game_id": game.id,
        },
    )


@api_view(["POST"])
def make_guess(request: Request) -> Response:  # noqa: PLR0911
    """Make guess."""
    if not request.user.is_authenticated:
        return Response({"error": "Пользователь не авторизован"}, status=401)

    game_id = request.data.get("game_id")
    guess = request.data.get("word")

    if not game_id or not guess:
        return Response({"error": "Нужно передать game_id и word"}, status=400)

    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return Response({"error": "Игра не найдена"}, status=404)

    if game.is_finished:
        return Response({"error": "Игра уже закончена"}, status=400)

    guess = normalize_word(guess)
    answer = normalize_word(game.term.word)

    if len(guess) != len(answer):
        return Response({"error": "Слово должно быть такой же длины"}, status=400)

    if not AllowedWord.objects.filter(word=guess).exists():
        return Response({"error": "Такого слова нет в словаре"}, status=400)

    result = compare_words(guess, answer)
    result_data = [asdict(item) for item in result]

    game.attempts += 1

    if guess == answer:
        game.is_finished = True
        game.is_won = True

        profile = Profile.objects.get(user=game.user)
        profile.rating += len(answer)
        profile.save()
    elif game.attempts >= game.max_attempts:
        game.is_finished = True
        game.is_won = False

    game.save()
    response = {
        "result": result_data,
        "attempts": game.attempts,
        "attempts_left": game.max_attempts - game.attempts,
        "is_finished": game.is_finished,
        "is_won": game.is_won,
    }

    if game.is_finished:
        response["answer"] = game.term.word
        response["definition"] = game.term.definition

    return Response(response)


@api_view(["GET"])
def leaderboard(request: Request) -> Response:
    """Leaderboard."""
    if not request.user.is_authenticated:
        return Response({"error": "Пользователь не авторизован"}, status=401)

    offset = int(request.query_params.get("offset", 0))
    limit = int(request.query_params.get("limit", 20))

    profiles = Profile.objects.order_by("-rating")[offset : offset + limit]
    data = [
        {
            "username": profile.user.username,
            "rating": profile.rating,
        }
        for profile in profiles
    ]
    return Response(data)


@api_view(["GET"])
def definition(request: Request) -> Response:
    """Get definition."""
    if not request.user.is_authenticated:
        return Response({"error": "Пользователь не авторизован"}, status=401)

    word = request.query_params.get("word")
    if not word:
        return Response({"error": "Нужно передать word"}, status=400)
    
    try:
        term = Term.objects.get(word=word)
    except Term.DoesNotExist:
        return Response({"error": "Слово не найдено"}, status=404)
    
    return Response({"word": word, "theme": term.theme, "definition": term.definition})
