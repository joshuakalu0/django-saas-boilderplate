from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django_tenants.utils import get_public_schema_name, tenant_context

from common.constants import AuditAction, MembershipRole, PlanCode, SubscriptionStatus
from common.utils import slugify_schema_name
from tenants.models import Domain, Organization


def create_tenant(
    *,
    organization_name: str,
    organization_slug: str,
    user_name: str,
    user_email: str,
    password: str,
):
    from accounts.models import OrganizationAccess, User
    from billing.models import Subscription
    from billing.services import create_or_get_stripe_customer_id
    from workspace.models import AuditLog, Membership

    slug = organization_slug.strip().lower()
    schema_name = slugify_schema_name(slug)
    domain_name = f"{slug}.{settings.PRIMARY_DOMAIN}"

    if Organization.objects.filter(slug=slug).exists():
        raise ValidationError("An organization with that slug already exists.")
    if User.objects.filter(email__iexact=user_email).exists():
        raise ValidationError("A user with that email address already exists.")

    with transaction.atomic():
        user = User.objects.create_user(email=user_email, password=password, name=user_name)
        organization = Organization.objects.create(
            name=organization_name,
            slug=slug,
            schema_name=schema_name,
        )
        Domain.objects.create(tenant=organization, domain=domain_name, is_primary=True)
        OrganizationAccess.objects.create(
            user=user,
            organization=organization,
            role=MembershipRole.OWNER,
            is_default=True,
            is_active=True,
        )
        Subscription.objects.create(
            organization=organization,
            stripe_customer_id=create_or_get_stripe_customer_id(organization, user.email),
            plan=PlanCode.FREE,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=3650),
        )

    with tenant_context(organization):
        Membership.objects.create(user_id=user.id, role=MembershipRole.OWNER, is_active=True)
        AuditLog.objects.create(
            actor_id=user.id,
            action=AuditAction.TENANT_CREATED,
            target_id=str(organization.id),
            metadata={"organization_slug": organization.slug},
        )

    return organization, user


def ensure_public_tenant():
    public_schema = get_public_schema_name()
    public_tenant, created = Organization.objects.get_or_create(
        schema_name=public_schema,
        defaults={"name": "Booster Public", "slug": "app"},
    )
    Domain.objects.get_or_create(
        tenant=public_tenant,
        domain=settings.PUBLIC_HOST,
        defaults={"is_primary": True},
    )
    return public_tenant, created
