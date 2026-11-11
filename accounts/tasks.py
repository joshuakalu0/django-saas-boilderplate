from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accounts.models import EmailVerification, PasswordResetToken
from common.utils import build_public_url


@shared_task
def send_verification_email_task(user_id: int, token: str):
    from accounts.models import User

    user = User.objects.get(id=user_id)
    verify_url = build_public_url(f"/auth/verify-email/?token={token}")
    send_mail(
        "Verify your Booster account",
        f"Hello {user.name}, verify your account by visiting {verify_url}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@shared_task
def send_password_reset_email_task(user_id: int, token: str):
    from accounts.models import User

    user = User.objects.get(id=user_id)
    reset_url = build_public_url(f"/auth/password-reset/{token}/")
    send_mail(
        "Reset your Booster password",
        f"Reset your password by visiting {reset_url}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@shared_task
def cleanup_expired_account_tokens():
    EmailVerification.objects.filter(expires_at__lt=timezone.now()).delete()
    PasswordResetToken.objects.filter(expires_at__lt=timezone.now()).delete()
