from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import FormView, TemplateView

from accounts.forms import ProfileForm
from common.constants import MembershipRole
from common.mixins import (
    TenantLoginRequiredMixin,
    TenantRequiredContextMixin,
    TenantRoleRequiredMixin,
)
from workspace.forms import InvitationForm, MemberRoleForm, OwnershipTransferForm, ProjectForm
from workspace.models import AuditLog, Invitation, Membership, Project
from workspace.services import (
    accept_invitation,
    create_project,
    get_members_with_users,
    invite_member,
    remove_member,
    transfer_ownership,
    update_member_role,
)


class DashboardView(TenantLoginRequiredMixin, TenantRequiredContextMixin, TemplateView):
    template_name = "workspace/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = Project.objects.all()[:5]
        context["member_count"] = Membership.objects.filter(is_active=True).count()
        context["recent_audit_logs"] = AuditLog.objects.all()[:10]
        return context


class MembersView(TenantRoleRequiredMixin, TenantRequiredContextMixin, TemplateView):
    template_name = "workspace/members.html"
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.MEMBER}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = get_members_with_users()
        context["invite_form"] = InvitationForm()
        context["ownership_form"] = OwnershipTransferForm()
        return context


class InviteMemberView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def post(self, request, *args, **kwargs):
        form = InvitationForm(request.POST)
        if form.is_valid():
            try:
                invite_member(
                    request.tenant,
                    request.user,
                    form.cleaned_data["email"],
                    form.cleaned_data["role"],
                )
                messages.success(request, "Invitation sent.")
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, form.errors.as_text())
        return redirect("workspace:members")


class AcceptInvitationView(View):
    template_name = "workspace/accept_invitation.html"

    def get(self, request, token, *args, **kwargs):
        invite = get_object_or_404(Invitation, token=token)
        return render(request, self.template_name, {"invite": invite})

    def post(self, request, token, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        name = request.POST.get("name", "")
        password = request.POST.get("password", "")
        try:
            accepted_user = accept_invitation(
                request.tenant, token, user=user, name=name, password=password
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("workspace:members")
        if not request.user.is_authenticated:
            from accounts.services import login_user

            login_user(request, accepted_user)
        messages.success(request, "You have joined the workspace.")
        return HttpResponseRedirect("/")


class UpdateMemberRoleView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def post(self, request, user_id, *args, **kwargs):
        member = get_object_or_404(Membership, user_id=user_id)
        form = MemberRoleForm(request.POST)
        if form.is_valid():
            try:
                update_member_role(request.user, member, form.cleaned_data["role"])
                messages.success(request, "Member role updated.")
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, form.errors.as_text())
        return redirect("workspace:members")


class RemoveMemberView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def post(self, request, user_id, *args, **kwargs):
        member = get_object_or_404(Membership, user_id=user_id)
        try:
            remove_member(request.user, member)
            messages.success(request, "Member removed.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        return redirect("workspace:members")


class TransferOwnershipView(TenantRoleRequiredMixin, View):
    required_roles = {MembershipRole.OWNER}

    def post(self, request, *args, **kwargs):
        form = OwnershipTransferForm(request.POST)
        if form.is_valid():
            try:
                transfer_ownership(request.user, form.cleaned_data["user_id"])
                messages.success(request, "Ownership transferred.")
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, form.errors.as_text())
        return redirect("workspace:members")


class ProjectsView(TenantLoginRequiredMixin, TenantRequiredContextMixin, FormView):
    form_class = ProjectForm
    template_name = "workspace/projects.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = Project.objects.all()
        return context

    def form_valid(self, form):
        try:
            create_project(
                self.request.user,
                form.cleaned_data["name"],
                form.cleaned_data.get("description", ""),
            )
            messages.success(self.request, "Project created.")
        except ValidationError as exc:
            messages.error(self.request, str(exc))
        return redirect("workspace:projects")


class AuditLogView(TenantRoleRequiredMixin, TenantRequiredContextMixin, TemplateView):
    template_name = "workspace/audit_log.html"
    required_roles = {MembershipRole.OWNER, MembershipRole.ADMIN}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["audit_logs"] = AuditLog.objects.all()
        return context


class ProfileView(TenantLoginRequiredMixin, TenantRequiredContextMixin, FormView):
    template_name = "accounts/profile.html"
    form_class = ProfileForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Profile saved.")
        return redirect("workspace:profile")
