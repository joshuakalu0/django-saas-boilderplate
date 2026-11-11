from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import FormView, TemplateView

from billing.forms import ApiKeyCreateForm, CheckoutPlanForm
from billing.models import ApiKey
from billing.services import (
    create_api_key,
    create_checkout_session,
    create_customer_portal_session,
    revoke_api_key,
)
from common.constants import MembershipRole
from common.mixins import TenantRequiredContextMixin, TenantRoleRequiredMixin


class BillingOverviewView(TenantRoleRequiredMixin, TenantRequiredContextMixin, FormView):
    template_name = "billing/overview.html"
    form_class = CheckoutPlanForm
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscription"] = getattr(self.request.tenant, "subscription", None)
        context["api_key_form"] = ApiKeyCreateForm()
        context["api_keys"] = ApiKey.objects.filter(
            organization=self.request.tenant, is_active=True
        )
        return context

    def form_valid(self, form):
        try:
            session = create_checkout_session(self.request.tenant, form.cleaned_data["plan"])
        except ValidationError as exc:
            messages.error(self.request, str(exc))
            return redirect("billing:overview")
        return redirect(session["url"])


class CustomerPortalView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def post(self, request, *args, **kwargs):
        try:
            session = create_customer_portal_session(request.tenant)
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("billing:overview")
        return redirect(session["url"])


class ApiKeyCreateView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def post(self, request, *args, **kwargs):
        form = ApiKeyCreateForm(request.POST)
        if form.is_valid():
            _, raw_token = create_api_key(request.tenant, request.user, form.cleaned_data["name"])
            messages.success(request, f"API key created. Copy it now: {raw_token}")
        else:
            messages.error(request, form.errors.as_text())
        return redirect("billing:overview")


class ApiKeyRevokeView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def post(self, request, key_id, *args, **kwargs):
        api_key = get_object_or_404(ApiKey, id=key_id, organization=request.tenant)
        revoke_api_key(api_key, request.user.id)
        messages.success(request, "API key revoked.")
        return redirect("billing:overview")


class BillingSuccessView(TenantRoleRequiredMixin, TemplateView):
    template_name = "billing/success.html"
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}
