from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin

from common.constants import MembershipRole
from workspace.models import Membership


class TenantRequiredContextMixin(ContextMixin):
    @cached_property
    def membership(self):
        if not self.request.user.is_authenticated:
            return None
        return Membership.objects.filter(user_id=self.request.user.id, is_active=True).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["membership"] = self.membership
        return context


class TenantLoginRequiredMixin:
    def handle_unauthenticated(self, request):
        next_url = quote(request.get_full_path())
        login_url = f"{reverse('accounts:login')}?next={next_url}"
        host = settings.PUBLIC_HOST
        scheme = "https" if settings.SECURE_SSL_REDIRECT else "http"
        return redirect(f"{scheme}://{host}{login_url}")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        return self.handle_unauthenticated(request)


class TenantRoleRequiredMixin(TenantLoginRequiredMixin):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.MEMBER}

    @cached_property
    def membership(self):
        return Membership.objects.filter(user_id=self.request.user.id, is_active=True).first()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_unauthenticated(request)
        if not self.membership or self.membership.role not in self.required_roles:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
