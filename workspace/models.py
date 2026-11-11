import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from common.constants import INVITATION_EXPIRY_HOURS, MembershipRole
from common.models import TimeStampedModel


def invitation_expiry():
    return timezone.now() + timedelta(hours=INVITATION_EXPIRY_HOURS)


class Membership(TimeStampedModel):
    user_id = models.PositiveBigIntegerField(db_index=True)
    role = models.CharField(max_length=20, choices=MembershipRole.choices)
    joined_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["joined_at"]


class Project(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    created_by_id = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["name"]
        unique_together = ("slug",)


class Invitation(TimeStampedModel):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    role = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.MEMBER
    )
    invited_by_id = models.PositiveBigIntegerField()
    expires_at = models.DateTimeField(default=invitation_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_user_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_valid(self):
        return self.accepted_at is None and self.expires_at >= timezone.now()


class AuditLog(TimeStampedModel):
    actor_id = models.PositiveBigIntegerField()
    action = models.CharField(max_length=100)
    target_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
