from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

from billing.services import authenticate_api_key


class ApiKeyAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or len(header) != 2:
            return None
        raw_token = header[1].decode("utf-8")
        api_key = authenticate_api_key(raw_token)
        if not api_key:
            raise exceptions.AuthenticationFailed("Invalid API key.")
        tenant = getattr(request, "tenant", None)
        if tenant and getattr(tenant, "schema_name", "public") != "public":
            if api_key.organization_id != tenant.id:
                raise exceptions.AuthenticationFailed(
                    "That API key does not belong to this tenant."
                )
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])
        request.api_key = api_key
        return api_key.created_by, api_key


class HybridTenantAuthentication(authentication.BaseAuthentication):
    def __init__(self):
        self.jwt_auth = JWTAuthentication()
        self.api_key_auth = ApiKeyAuthentication()

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or len(header) != 2:
            return None
        raw_token = header[1].decode("utf-8")
        if raw_token.count(".") == 2:
            return self.jwt_auth.authenticate(request)
        return self.api_key_auth.authenticate(request)
