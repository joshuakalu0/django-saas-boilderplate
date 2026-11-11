from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.http import HttpResponseNotFound
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model, get_tenant_model


class HeaderAwareTenantMiddleware(TenantMainMiddleware):
    """Resolve tenants by hostname first, then fall back to a trusted header for local/API usage."""

    def get_tenant_from_header(self, request):
        header_name = settings.TENANT_HEADER_NAME
        slug = request.META.get(header_name)
        if not slug:
            return None
        tenant_model = get_tenant_model()
        return (
            tenant_model.objects.filter(slug=slug).first()
            or tenant_model.objects.filter(schema_name=slug).first()
        )

    def process_request(self, request):
        connection.set_schema_to_public()
        try:
            hostname = self.hostname_from_request(request)
        except DisallowedHost:
            return HttpResponseNotFound()

        domain_model = get_tenant_domain_model()
        try:
            tenant = self.get_tenant(domain_model, hostname)
        except domain_model.DoesNotExist:
            tenant = self.get_tenant_from_header(request)
            if tenant is None:
                return self.no_tenant_found(request, hostname)

        tenant.domain_url = hostname
        request.tenant = tenant
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)
