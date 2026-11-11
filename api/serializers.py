from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.models import OrganizationAccess, User
from billing.models import ApiKey, Subscription
from common.constants import MembershipRole, PlanCode
from workspace.models import AuditLog, Invitation, Membership, Project
from workspace.services import get_user


class RegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    organization_name = serializers.CharField(max_length=255)
    organization_slug = serializers.CharField(max_length=255, required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"].strip().lower(), password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class TokenRefreshInputSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class TokenVerifyInputSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True)


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "avatar", "email_verified_at")


class MeSerializer(serializers.Serializer):
    user = UserSerializer()
    organization = serializers.DictField()
    role = serializers.CharField()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name", "avatar")


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = ("user_id", "role", "joined_at", "is_active", "user")

    def get_user(self, obj):
        user = get_user(obj.user_id)
        if not user:
            return None
        return UserSerializer(user).data


class MemberRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=MembershipRole.choices)


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ("id", "email", "role", "token", "expires_at", "accepted_at", "created_at")
        read_only_fields = ("token", "expires_at", "accepted_at", "created_at")


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "slug", "description", "created_by_id", "created_at", "updated_at")
        read_only_fields = ("id", "slug", "created_by_id", "created_at", "updated_at")


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "actor_id", "action", "target_id", "metadata", "created_at")


class SubscriptionSerializer(serializers.ModelSerializer):
    limits = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "plan",
            "status",
            "stripe_customer_id",
            "stripe_subscription_id",
            "current_period_end",
            "limits",
        )

    def get_limits(self, obj):
        from billing.services import get_plan_limits

        return get_plan_limits(obj.plan)


class CheckoutSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=PlanCode.choices)


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ("id", "name", "last_used_at", "is_active", "created_at")


class ApiKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class OrganizationAccessSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationAccess
        fields = ("organization", "role", "is_default", "is_active")

    def get_organization(self, obj):
        return {
            "id": obj.organization_id,
            "name": obj.organization.name,
            "slug": obj.organization.slug,
            "domain": obj.organization.primary_domain,
        }
