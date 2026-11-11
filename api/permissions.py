from rest_framework.permissions import BasePermission

from common.constants import MembershipRole
from workspace.models import Membership


def get_membership(request):
    if hasattr(request, "membership") and request.membership:
        return request.membership
    membership = Membership.objects.filter(user_id=request.user.id, is_active=True).first()
    request.membership = membership
    return membership


class IsTenantAuthenticated(BasePermission):
    message = "You must be an active member of this tenant."

    def has_permission(self, request, view):
        tenant = getattr(request, "tenant", None)
        if not tenant or getattr(tenant, "schema_name", "public") == "public":
            return False
        if not request.user or not request.user.is_authenticated:
            return False
        return get_membership(request) is not None


class IsTenantAdmin(IsTenantAuthenticated):
    message = "You must be an admin or owner."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}


class IsTenantOwner(IsTenantAuthenticated):
    message = "You must be the owner."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.membership.role == MembershipRole.OWNER
