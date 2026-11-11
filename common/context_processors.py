from django.conf import settings

from billing.models import Subscription


def application_context(request):
    tenant = getattr(request, "tenant", None)
    subscription = None
    if tenant and getattr(tenant, "schema_name", "") != "public":
        subscription = Subscription.objects.filter(organization=tenant).first()
    return {
        "app_name": "Booster SaaS Django",
        "request_id": getattr(request, "request_id", None),
        "current_tenant": tenant,
        "current_subscription": subscription,
        "PUBLIC_HOST": settings.PUBLIC_HOST,
    }
