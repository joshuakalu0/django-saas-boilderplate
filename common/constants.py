from django.db import models


class MembershipRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    MEMBER = "MEMBER", "Member"


class PlanCode(models.TextChoices):
    FREE = "FREE", "Free"
    PRO = "PRO", "Pro"
    ENTERPRISE = "ENTERPRISE", "Enterprise"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAST_DUE = "PAST_DUE", "Past due"
    CANCELLED = "CANCELLED", "Cancelled"


class AuditAction(models.TextChoices):
    TENANT_CREATED = "tenant.created", "Tenant created"
    MEMBER_INVITED = "member.invited", "Member invited"
    MEMBER_JOINED = "member.joined", "Member joined"
    MEMBER_REMOVED = "member.removed", "Member removed"
    ROLE_CHANGED = "member.role_changed", "Member role changed"
    OWNERSHIP_TRANSFERRED = "tenant.ownership_transferred", "Ownership transferred"
    PROJECT_CREATED = "project.created", "Project created"
    SUBSCRIPTION_UPDATED = "billing.subscription_updated", "Subscription updated"
    API_KEY_CREATED = "api_key.created", "API key created"
    API_KEY_REVOKED = "api_key.revoked", "API key revoked"


PLAN_LIMITS = {
    PlanCode.FREE: {"max_members": 3, "max_projects": 5},
    PlanCode.PRO: {"max_members": 25, "max_projects": 100},
    PlanCode.ENTERPRISE: {"max_members": 999999, "max_projects": 999999},
}

EMAIL_VERIFICATION_EXPIRY_HOURS = 48
PASSWORD_RESET_EXPIRY_HOURS = 1
INVITATION_EXPIRY_HOURS = 48
REFRESH_TOKEN_BODY_HEADER = "HTTP_X_RETURN_REFRESH_TOKEN"
