import secrets
from urllib.parse import urljoin

from django.conf import settings
from django.utils.text import slugify

from common.constants import REFRESH_TOKEN_BODY_HEADER


def slugify_schema_name(value: str) -> str:
    slug = slugify(value).replace("-", "_")
    if not slug:
        raise ValueError("A valid schema name could not be generated from the provided value.")
    if slug == "public":
        raise ValueError("The schema name 'public' is reserved.")
    return slug


def build_tenant_url(tenant, path: str = "/") -> str:
    domain = tenant.primary_domain
    base = f"http://{domain}"
    if settings.SECURE_SSL_REDIRECT:
        base = f"https://{domain}"
    return urljoin(f"{base}/", path.lstrip("/"))


def build_public_url(path: str = "/") -> str:
    base = f"http://{settings.PUBLIC_HOST}"
    if settings.SECURE_SSL_REDIRECT:
        base = f"https://{settings.PUBLIC_HOST}"
    return urljoin(f"{base}/", path.lstrip("/"))


def token_string(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def wants_refresh_token_in_body(request) -> bool:
    value = request.META.get(REFRESH_TOKEN_BODY_HEADER, "")
    return str(value).lower() in {"1", "true", "yes"}
