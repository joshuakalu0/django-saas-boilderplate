from datetime import timedelta

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from billing.models import ApiKey, Subscription
from common.constants import PLAN_LIMITS, AuditAction, PlanCode, SubscriptionStatus
from common.utils import token_string
from workspace.models import AuditLog

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_plan_limits(plan: str):
    return PLAN_LIMITS[plan]


def assert_plan_allows_members(organization):
    subscription = get_or_create_subscription(organization)
    limits = get_plan_limits(subscription.plan)
    from workspace.models import Membership

    if Membership.objects.filter(is_active=True).count() >= limits["max_members"]:
        raise ValidationError("Your current plan has reached its member limit.")


def assert_plan_allows_projects(organization):
    subscription = get_or_create_subscription(organization)
    limits = get_plan_limits(subscription.plan)
    from workspace.models import Project

    if Project.objects.count() >= limits["max_projects"]:
        raise ValidationError("Your current plan has reached its project limit.")


def create_or_get_stripe_customer_id(organization, email: str):
    subscription = Subscription.objects.filter(organization=organization).first()
    if subscription and subscription.stripe_customer_id:
        return subscription.stripe_customer_id
    if not settings.STRIPE_SECRET_KEY:
        return f"local_{organization.slug}"
    customer = stripe.Customer.create(email=email, name=organization.name)
    return customer["id"]


def get_or_create_subscription(organization):
    return Subscription.objects.get_or_create(
        organization=organization,
        defaults={
            "stripe_customer_id": create_or_get_stripe_customer_id(organization, ""),
            "plan": PlanCode.FREE,
            "status": SubscriptionStatus.ACTIVE,
            "current_period_end": timezone.now() + timedelta(days=3650),
        },
    )[0]


def create_checkout_session(organization, plan: str):
    if plan == PlanCode.FREE:
        raise ValidationError("The Free plan does not require checkout.")
    price_id = settings.STRIPE_PRICE_IDS.get(plan)
    if not price_id:
        raise ValidationError("That plan is not configured.")
    subscription = get_or_create_subscription(organization)
    if not settings.STRIPE_SECRET_KEY:
        return {"url": settings.STRIPE_SUCCESS_URL}
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=subscription.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={"organization_id": str(organization.id), "plan": plan},
    )
    return session


def create_customer_portal_session(organization):
    subscription = get_or_create_subscription(organization)
    if not settings.STRIPE_SECRET_KEY:
        return {"url": settings.STRIPE_CANCEL_URL}
    session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=settings.STRIPE_CANCEL_URL,
    )
    return session


def create_api_key(organization, created_by, name: str):
    raw_token = f"bsk_{token_string(24)}"
    api_key = ApiKey.objects.create(
        organization=organization,
        created_by=created_by,
        name=name,
        key_hash=ApiKey.hash_token(raw_token),
    )
    AuditLog.objects.create(
        actor_id=created_by.id,
        action=AuditAction.API_KEY_CREATED,
        target_id=str(api_key.id),
        metadata={"name": name},
    )
    return api_key, raw_token


def authenticate_api_key(raw_token: str):
    return (
        ApiKey.objects.filter(key_hash=ApiKey.hash_token(raw_token), is_active=True)
        .select_related("organization", "created_by")
        .first()
    )


def revoke_api_key(api_key: ApiKey, actor_id: int):
    api_key.is_active = False
    api_key.save(update_fields=["is_active"])
    AuditLog.objects.create(
        actor_id=actor_id,
        action=AuditAction.API_KEY_REVOKED,
        target_id=str(api_key.id),
        metadata={"name": api_key.name},
    )


def update_subscription_from_event(
    organization_id: int,
    *,
    plan: str,
    status: str,
    stripe_subscription_id: str = "",
):
    subscription = Subscription.objects.get(organization_id=organization_id)
    subscription.plan = plan
    subscription.status = status
    subscription.stripe_subscription_id = (
        stripe_subscription_id or subscription.stripe_subscription_id
    )
    subscription.current_period_end = timezone.now() + timedelta(days=30)
    subscription.save()


def handle_stripe_webhook_payload(payload: dict):
    event_type = payload.get("type")
    data = payload.get("data", {}).get("object", {})
    organization_id = int(data.get("metadata", {}).get("organization_id", 0) or 0)
    if not organization_id:
        return
    if event_type == "checkout.session.completed":
        update_subscription_from_event(
            organization_id,
            plan=PlanCode.PRO,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id=data.get("subscription", ""),
        )
    elif event_type == "invoice.payment_succeeded":
        update_subscription_from_event(
            organization_id, plan=PlanCode.PRO, status=SubscriptionStatus.ACTIVE
        )
    elif event_type == "invoice.payment_failed":
        update_subscription_from_event(
            organization_id, plan=PlanCode.PRO, status=SubscriptionStatus.PAST_DUE
        )
    elif event_type == "customer.subscription.deleted":
        update_subscription_from_event(
            organization_id, plan=PlanCode.FREE, status=SubscriptionStatus.CANCELLED
        )
