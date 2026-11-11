from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import EmailVerification, OrganizationAccess, PasswordResetToken, User
from accounts.tasks import send_password_reset_email_task, send_verification_email_task
from common.utils import build_public_url, build_tenant_url, wants_refresh_token_in_body


def issue_token_pair(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def blacklist_user_tokens(user):
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
    except Exception:
        return

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def apply_refresh_token_transport(request, response, refresh_token: str):
    if wants_refresh_token_in_body(request):
        return response, refresh_token

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        samesite="Lax",
        secure=settings.SESSION_COOKIE_SECURE,
        domain=settings.SESSION_COOKIE_DOMAIN,
    )
    return response, None


def clear_refresh_cookie(response):
    response.delete_cookie("refresh_token")


def create_email_verification(user: User):
    verification = EmailVerification.objects.create(user=user)
    send_verification_email_task.delay(user.id, str(verification.token))
    return verification


def create_password_reset_token(user: User):
    reset_token = PasswordResetToken.objects.create(user=user)
    send_password_reset_email_task.delay(user.id, str(reset_token.token))
    return reset_token


def resolve_user_tenants(user: User):
    return OrganizationAccess.objects.filter(user=user, is_active=True).select_related(
        "organization"
    )


def primary_tenant_redirect(user: User, path: str = "/") -> str:
    access = (
        resolve_user_tenants(user).filter(is_default=True).first()
        or resolve_user_tenants(user).first()
    )
    if access:
        return build_tenant_url(access.organization, path)
    return build_public_url("/")


def authenticate_by_email(email: str, password: str):
    return authenticate(username=email.strip().lower(), password=password)


def login_user(request, user: User):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")


def logout_user(request):
    if request.user.is_authenticated:
        blacklist_user_tokens(request.user)
    logout(request)


def verify_email_token(token: str):
    verification = EmailVerification.objects.filter(token=token).select_related("user").first()
    if not verification or not verification.is_valid:
        raise ValidationError("That verification link is invalid or expired.")
    verification.consumed_at = timezone.now()
    verification.save(update_fields=["consumed_at"])
    verification.user.email_verified_at = timezone.now()
    verification.user.save(update_fields=["email_verified_at"])
    return verification.user


def reset_password(token: str, password: str):
    reset_token = PasswordResetToken.objects.filter(token=token).select_related("user").first()
    if not reset_token or not reset_token.is_valid:
        raise ValidationError("That password reset link is invalid or expired.")
    user = reset_token.user
    user.set_password(password)
    user.save(update_fields=["password"])
    reset_token.consumed_at = timezone.now()
    reset_token.save(update_fields=["consumed_at"])
    blacklist_user_tokens(user)
    return user


def set_default_organization(user: User, organization_id: int):
    accesses = OrganizationAccess.objects.filter(user=user)
    accesses.update(is_default=False)
    accesses.filter(organization_id=organization_id).update(is_default=True)


def redirect_to_next_or_default(request, user: User):
    next_path = request.GET.get("next")
    if next_path:
        return HttpResponseRedirect(next_path)
    return HttpResponseRedirect(primary_tenant_redirect(user))


def verification_banner_query():
    return urlencode({"verified": "1"})
