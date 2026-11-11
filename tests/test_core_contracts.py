import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import override_settings

from accounts.models import User
from accounts.services import issue_token_pair
from api.exceptions import custom_exception_handler
from billing.models import ApiKey
from billing.services import get_plan_limits
from common.constants import PlanCode
from common.utils import build_public_url, slugify_schema_name


def test_slugify_schema_name_normalizes_and_blocks_public():
    assert slugify_schema_name("Acme Team") == "acme_team"
    with pytest.raises(ValueError):
        slugify_schema_name("public")


def test_api_key_hash_is_stable():
    token = "bsk_test_token"
    assert ApiKey.hash_token(token) == ApiKey.hash_token(token)


def test_plan_limits_match_free_tier_contract():
    limits = get_plan_limits(PlanCode.FREE)
    assert limits["max_members"] == 3
    assert limits["max_projects"] == 5


@override_settings(PUBLIC_HOST="app.lvh.me", SECURE_SSL_REDIRECT=False)
def test_build_public_url_uses_public_host():
    assert build_public_url("/auth/login/") == "http://app.lvh.me/auth/login/"


@pytest.mark.django_db
def test_issue_token_pair_returns_access_and_refresh():
    user = User.objects.create_user(email="owner@example.com", password="secret123", name="Owner")
    tokens = issue_token_pair(user)
    assert "access" in tokens
    assert "refresh" in tokens


def test_custom_exception_handler_wraps_django_validation_error():
    response = custom_exception_handler(DjangoValidationError("boom"), {})
    assert response.status_code == 400
    assert response.data["error"] == "validation_error"
