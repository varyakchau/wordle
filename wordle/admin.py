"""Wordle admin."""

from django.contrib import admin

# Register your models here.
from .models import Game, Profile, Term

admin.site.register(Term)
admin.site.register(Game)
admin.site.register(Profile)
