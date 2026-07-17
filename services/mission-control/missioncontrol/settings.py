"""Django settings for the mission-control service.

Values that change between environments (secret key, debug, allowed hosts, the
SQLite file location) are read from environment variables so the same image can
run locally and in a container. The container entrypoint runs ``migrate`` at
start against a SQLite file on a mounted volume (see the Dockerfile / README).
"""

from __future__ import annotations

import os
from pathlib import Path

# services/mission-control/missioncontrol/settings.py -> services/mission-control
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: an insecure default is fine for scaffolding; override in any real
# deployment via the environment.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-mission-control-scaffolding-key-change-me",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

# Default to "*" so the container is reachable without per-host wiring on this
# scaffolding cut; narrow this via DJANGO_ALLOWED_HOSTS in a real deployment.
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "logs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "missioncontrol.urls"

# Templates are discovered via APP_DIRS (logs/templates/), so no explicit DIRS.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "missioncontrol.wsgi.application"

# Single-file SQLite. The path is env-driven so the container can point it at a
# mounted volume for persistence.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
