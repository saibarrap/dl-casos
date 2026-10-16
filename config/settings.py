"""
Configuracion de Django para el proyecto DL Casos (RC Medica) — MVP Sprint 1.

La configuracion sensible se toma de variables de entorno (.env). Nunca se
guardan credenciales en el repositorio.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga de variables de entorno desde un archivo .env en la raiz del proyecto.
load_dotenv(BASE_DIR / ".env")


def _env_bool(nombre: str, por_defecto: str = "False") -> bool:
    return os.getenv(nombre, por_defecto).strip().lower() in {"1", "true", "yes", "si", "on"}


def _env_list(nombre: str, por_defecto: str = "") -> list[str]:
    valor = os.getenv(nombre, por_defecto)
    return [item.strip() for item in valor.split(",") if item.strip()]


# SECURITY WARNING: en produccion defina SECRET_KEY por entorno.
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-insecure-key-cambiar-en-produccion",
)

DEBUG = _env_bool("DEBUG", "True")

ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "casos.apps.CasosConfig",
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

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Base de datos: MySQL 8.0 con InnoDB. Las reglas de integridad viven en la BD.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "dl_casos"),
        "USER": os.getenv("DB_USER", "dl_casos"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            # sql_mode estricto para que MySQL rechace datos invalidos.
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE'",
        },
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}


# Validacion de contrasenas (ademas del hash por defecto de Django).
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Hashers por defecto de Django (PBKDF2). Las contrasenas se guardan con hash.
# (No se sobrescribe PASSWORD_HASHERS para conservar el default seguro.)


# Internacionalizacion: espanol de Colombia y zona horaria de Bogota.
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# Archivos estaticos
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Contrasena de los usuarios demo (comandos de seed). Nunca se versiona.
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "")
