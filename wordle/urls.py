"""URLs for the wordle app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("auth/", views.auth_page, name="auth"),
    path("menu/", views.menu, name="menu"),
    path("game/<int:word_length>/", views.game, name="game"),
    path("rating/", views.rating, name="rating"),
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login, name="login"),
    path("start-game/", views.start_game, name="start-game"),
    path("make-guess/", views.make_guess, name="make-guess"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("definition/", views.definition, name="definition"),
]
