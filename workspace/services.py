from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import OrganizationAccess, User
from billing.services import assert_plan_allows_members, assert_plan_allows_projects
from common.constants import AuditAction, MembershipRole
from common.utils import build_tenant_url
from workspace.models import AuditLog, Invitation, Membership, Project
from workspace.tasks import send_invitation_email_task


def current_organization_accesses():
    return OrganizationAccess.objects.filter(organization__schema_name=connection.schema_name)


def get_user(user_id: int):
    return User.objects.filter(id=user_id).first()


def get_members_with_users():
    members = list(Membership.objects.filter(is_active=True))
    users = User.objects.in_bulk([member.user_id for member in members])
    return [(member, users.get(member.user_id)) for member in members]


def get_membership_for_user(user_id: int):
    return Membership.objects.filter(user_id=user_id, is_active=True).first()


def log_action(actor_id: int, action: str, target_id: str = "", metadata=None):
    return AuditLog.objects.create(
        actor_id=actor_id,
        action=action,
        target_id=target_id,
        metadata=metadata or {},
    )


def require_verified_user(user: User):
    if not user.is_email_verified:
        raise ValidationError("You must verify your email address before inviting members.")


def invite_member(tenant, actor: User, email: str, role: str):
    require_verified_user(actor)
    assert_plan_allows_members(tenant)
    invite = Invitation.objects.create(
        email=email.strip().lower(), role=role, invited_by_id=actor.id
    )
    invite_url = build_tenant_url(tenant, f"/invitations/accept/{invite.token}/")
    send_invitation_email_task.delay(invite.email, invite_url)
    log_action(
        actor.id,
        AuditAction.MEMBER_INVITED,
        str(invite.token),
        {"email": invite.email, "role": role},
    )
    return invite


def accept_invitation(tenant, token, user=None, name=None, password=None):
    assert_plan_allows_members(tenant)
    invite = Invitation.objects.filter(token=token).first()
    if not invite or not invite.is_valid:
        raise ValidationError("That invitation is invalid or expired.")

    target_user = user or User.objects.filter(email__iexact=invite.email).first()
    if not target_user:
        if not password or not name:
            raise ValidationError("Name and password are required to accept this invitation.")
        target_user = User.objects.create_user(email=invite.email, password=password, name=name)

    membership, created = Membership.objects.get_or_create(
        user_id=target_user.id,
        defaults={"role": invite.role, "is_active": True},
    )
    if not created and membership.is_active:
        raise ValidationError("That user is already a member of this workspace.")

    membership.role = invite.role
    membership.is_active = True
    membership.save()

    OrganizationAccess.objects.update_or_create(
        user=target_user,
        organization=tenant,
        defaults={"role": invite.role, "is_active": True},
    )

    invite.accepted_at = timezone.now()
    invite.accepted_user_id = target_user.id
    invite.save(update_fields=["accepted_at", "accepted_user_id"])
    log_action(
        target_user.id, AuditAction.MEMBER_JOINED, str(target_user.id), {"email": invite.email}
    )
    return target_user


def update_member_role(actor: User, member: Membership, role: str):
    actor_membership = get_membership_for_user(actor.id)
    if not actor_membership or actor_membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN,
    }:
        raise PermissionDenied("You do not have permission to change member roles.")
    if member.role == MembershipRole.OWNER and actor_membership.role != MembershipRole.OWNER:
        raise PermissionDenied("Only the workspace owner can modify the owner role.")

    member.role = role
    member.save(update_fields=["role"])
    current_organization_accesses().filter(user_id=member.user_id).update(role=role)
    log_action(actor.id, AuditAction.ROLE_CHANGED, str(member.user_id), {"role": role})
    return member


def remove_member(actor: User, member: Membership):
    actor_membership = get_membership_for_user(actor.id)
    if not actor_membership or actor_membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN,
    }:
        raise PermissionDenied("You do not have permission to remove members.")
    if member.role == MembershipRole.OWNER:
        raise ValidationError("The workspace owner cannot be removed.")

    member.is_active = False
    member.save(update_fields=["is_active"])
    current_organization_accesses().filter(user_id=member.user_id).update(is_active=False)
    log_action(actor.id, AuditAction.MEMBER_REMOVED, str(member.user_id))


def transfer_ownership(actor: User, new_owner_user_id: int):
    owner_membership = get_membership_for_user(actor.id)
    new_owner = Membership.objects.filter(user_id=new_owner_user_id, is_active=True).first()
    if not owner_membership or owner_membership.role != MembershipRole.OWNER:
        raise PermissionDenied("Only the workspace owner can transfer ownership.")
    if not new_owner:
        raise ValidationError("The selected user is not an active workspace member.")

    with transaction.atomic():
        owner_membership.role = MembershipRole.ADMIN
        owner_membership.save(update_fields=["role"])
        new_owner.role = MembershipRole.OWNER
        new_owner.save(update_fields=["role"])
        current_organization_accesses().filter(user_id=actor.id).update(role=MembershipRole.ADMIN)
        current_organization_accesses().filter(user_id=new_owner.user_id).update(
            role=MembershipRole.OWNER, is_default=True
        )
    log_action(
        actor.id,
        AuditAction.OWNERSHIP_TRANSFERRED,
        str(new_owner_user_id),
        {"from_user_id": actor.id, "to_user_id": new_owner_user_id},
    )


def create_project(actor: User, name: str, description: str = ""):
    from django.db import connection

    from tenants.models import Organization

    assert_plan_allows_projects(Organization.objects.get(schema_name=connection.schema_name))
    project = Project.objects.create(
        name=name,
        slug=slugify(name),
        description=description,
        created_by_id=actor.id,
    )
    log_action(actor.id, AuditAction.PROJECT_CREATED, str(project.id), {"name": name})
    return project
