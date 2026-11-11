from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from workspace.models import Invitation


@shared_task
def send_invitation_email_task(email: str, invite_url: str):
    send_mail(
        "You were invited to a Booster workspace",
        f"You can accept the invitation here: {invite_url}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


@shared_task
def cleanup_expired_invitations():
    Invitation.objects.filter(expires_at__lt=timezone.now(), accepted_at__isnull=True).delete()
