from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import FormView, TemplateView

from accounts.forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    ProfileForm,
    RegistrationForm,
)
from accounts.models import OrganizationAccess, User
from accounts.services import (
    create_email_verification,
    create_password_reset_token,
    login_user,
    logout_user,
    redirect_to_next_or_default,
    reset_password,
    resolve_user_tenants,
    set_default_organization,
    verify_email_token,
)
from common.mixins import TenantLoginRequiredMixin, TenantRequiredContextMixin
from common.utils import build_tenant_url
from tenants.services import create_tenant


class PublicHomeView(TemplateView):
    template_name = "common/public_home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            accesses = resolve_user_tenants(request.user)
            if accesses.count() == 1:
                return HttpResponseRedirect(build_tenant_url(accesses.first().organization))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["organizations"] = resolve_user_tenants(self.request.user)
        return context


class RegisterView(FormView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"

    def form_valid(self, form):
        organization, user = create_tenant(
            organization_name=form.cleaned_data["organization_name"],
            organization_slug=form.cleaned_data["organization_slug"],
            user_name=form.cleaned_data["name"],
            user_email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        create_email_verification(user)
        login_user(self.request, user)
        messages.success(self.request, "Your workspace is ready.")
        return HttpResponseRedirect(build_tenant_url(organization))


class LoginView(FormView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        user = form.cleaned_data["user"]
        login_user(self.request, user)
        accesses = resolve_user_tenants(user)
        if accesses.count() > 1:
            return redirect("accounts:tenant-select")
        return redirect_to_next_or_default(self.request, user)


class TenantSelectView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/tenant_select.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organizations"] = resolve_user_tenants(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        organization_id = request.POST.get("organization_id")
        access = get_object_or_404(
            OrganizationAccess, user=request.user, organization_id=organization_id, is_active=True
        )
        set_default_organization(request.user, access.organization_id)
        return HttpResponseRedirect(build_tenant_url(access.organization))


class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout_user(request)
        response = redirect("accounts:login")
        response.delete_cookie("refresh_token")
        return response

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class VerifyEmailView(View):
    def get(self, request, *args, **kwargs):
        token = request.GET.get("token", "")
        try:
            verify_email_token(token)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("accounts:login")
        messages.success(request, "Your email address has been verified.")
        return redirect("accounts:login")


class PasswordResetRequestView(FormView):
    form_class = PasswordResetRequestForm
    template_name = "accounts/password_reset_request.html"

    def form_valid(self, form):
        user = User.objects.filter(email__iexact=form.cleaned_data["email"]).first()
        if user:
            create_password_reset_token(user)
        messages.success(self.request, "If that account exists, a reset link has been sent.")
        return redirect("accounts:login")


class PasswordResetConfirmView(FormView):
    form_class = PasswordResetConfirmForm
    template_name = "accounts/password_reset_confirm.html"

    def dispatch(self, request, *args, **kwargs):
        self.token = kwargs["token"]
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        reset_password(self.token, form.cleaned_data["password"])
        messages.success(self.request, "Your password has been reset. Please log in.")
        return redirect("accounts:login")


class ProfileView(TenantLoginRequiredMixin, TenantRequiredContextMixin, FormView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your profile has been updated.")
        return redirect("workspace:profile")


def tenant_access_denied(request):
    return render(request, "common/access_denied.html", status=403)
