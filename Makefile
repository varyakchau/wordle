.PHONY: start test migrate

start:
	uv run python manage.py makemigrations wordle --no-input
	uv run python manage.py migrate
	uv run python manage.py import_words
	uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2

test:
	uv run python manage.py makemigrations wordle --no-input
	uv run python manage.py migrate
	uv run python manage.py test

migrate:
	uv run python manage.py makemigrations wordle --no-input
	uv run python manage.py migrate
