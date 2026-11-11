from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-secret-key")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost", ".lvh.me"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
DJANGO_ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="Booster <noreply@booster.local>")
PRIMARY_DOMAIN = env("DJANGO_PRIMARY_DOMAIN", default="lvh.me")
PUBLIC_HOST = env("DJANGO_PUBLIC_HOST", default="app.lvh.me")
SHOW_PUBLIC_IF_NO_TENANT_FOUND = env.bool("DJANGO_SHOW_PUBLIC_IF_NO_TENANT_FOUND", default=True)
TENANT_HEADER_NAME = env("DJANGO_TENANT_HEADER", default="HTTP_X_TENANT_SLUG")

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgresql://postgres:postgres@localhost:5432/booster",
    )
}
DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

SHARED_APPS = (
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.sites",
    "django_htmx",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "common",
    "tenants",
    "accounts",
    "billing",
    "api",
)

TENANT_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django_htmx",
    "workspace",
)

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenants.Organization"
TENANT_DOMAIN_MODEL = "tenants.Domain"
PUBLIC_SCHEMA_URLCONF = "config.urls_public"
ROOT_URLCONF = "config.urls_tenant"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "accounts.User"
SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/auth/login/"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True

MIDDLEWARE = [
    "tenants.middleware.HeaderAwareTenantMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "common.middleware.RequestContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.application_context",
            ],
            "loaders": [
                "django_tenants.template.loaders.filesystem.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]

MULTITENANT_TEMPLATE_DIRS = [str(BASE_DIR / "templates" / "tenants" / "%s")]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_FINDERS = [
    "django_tenants.staticfiles.finders.TenantFileSystemFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
MULTITENANT_STATICFILES_DIRS = [str(BASE_DIR / "tenants" / "%s" / "static")]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django_tenants.staticfiles.storage.TenantStaticFilesStorage"},
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.HybridTenantAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "api.throttling.BurstRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/hour",
        "user": "1000/hour",
        "burst": "60/minute",
    },
    "EXCEPTION_HANDLER": "api.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Booster SaaS Django API",
    "DESCRIPTION": "Schema-based multi-tenant SaaS API with JWT and API key auth.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)
SESSION_COOKIE_DOMAIN = env("DJANGO_SESSION_COOKIE_DOMAIN", default=None)
CSRF_COOKIE_DOMAIN = env("DJANGO_CSRF_COOKIE_DOMAIN", default=None)
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)

CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default=env("REDIS_URL", default="redis://redis:6379/1")
)
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default=env("REDIS_URL", default="redis://redis:6379/2"),
)
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_BEAT_SCHEDULER = "celery.beat:PersistentScheduler"
CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-account-tokens": {
        "task": "accounts.tasks.cleanup_expired_account_tokens",
        "schedule": 3600,
    },
    "cleanup-expired-invitations": {
        "task": "workspace.tasks.cleanup_expired_invitations",
        "schedule": 3600,
    },
}

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PRICE_IDS = {
    "FREE": env("STRIPE_FREE_PRICE_ID", default="price_free"),
    "PRO": env("STRIPE_PRO_PRICE_ID", default=""),
    "ENTERPRISE": env("STRIPE_ENTERPRISE_PRICE_ID", default=""),
}
STRIPE_SUCCESS_URL = env("STRIPE_SUCCESS_URL", default="http://app.lvh.me:8000/billing/success/")
STRIPE_CANCEL_URL = env("STRIPE_CANCEL_URL", default="http://app.lvh.me:8000/billing/")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "tenant_context": {"()": "django_tenants.log.TenantContextFilter"},
    },
    "formatters": {
        "verbose": {
            "format": (
                "[%(schema_name)s:%(domain_url)s] "
                "%(levelname)s %(asctime)s %(name)s %(message)s"
            )
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["tenant_context"],
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
