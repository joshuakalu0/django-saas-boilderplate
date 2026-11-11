import hashlib

from django.db import models

from common.constants import PlanCode, SubscriptionStatus
from common.models import TimeStampedModel


class Subscription(TimeStampedModel):
    organization = models.OneToOneField(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    plan = models.CharField(max_length=20, choices=PlanCode.choices, default=PlanCode.FREE)
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    current_period_end = models.DateTimeField(null=True, blank=True)


class ApiKey(TimeStampedModel):
    organization = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="created_api_keys",
    )
    name = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=64, unique=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
