import json

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenVerifySerializer

from accounts.models import User
from accounts.services import (
    apply_refresh_token_transport,
    blacklist_user_tokens,
    create_email_verification,
    create_password_reset_token,
    issue_token_pair,
    reset_password,
    resolve_user_tenants,
    verify_email_token,
)
from api.permissions import IsTenantAdmin, IsTenantAuthenticated
from api.serializers import (
    ApiKeyCreateSerializer,
    ApiKeySerializer,
    AuditLogSerializer,
    CheckoutSerializer,
    InvitationAcceptSerializer,
    InvitationSerializer,
    LoginSerializer,
    MemberRoleUpdateSerializer,
    MemberSerializer,
    MeSerializer,
    OrganizationAccessSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    ProjectSerializer,
    RegistrationSerializer,
    SubscriptionSerializer,
    TokenRefreshInputSerializer,
    TokenVerifyInputSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from billing.models import ApiKey
from billing.services import (
    create_api_key,
    create_checkout_session,
    create_customer_portal_session,
    get_or_create_subscription,
    revoke_api_key,
)
from billing.tasks import process_stripe_webhook_task
from common.constants import MembershipRole
from common.responses import api_success
from tenants.services import create_tenant
from workspace.models import AuditLog, Invitation, Membership, Project
from workspace.services import (
    accept_invitation,
    create_project,
    invite_member,
    remove_member,
    update_member_role,
)


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization, user = create_tenant(
            organization_name=serializer.validated_data["organization_name"],
            organization_slug=serializer.validated_data.get("organization_slug")
            or serializer.validated_data["organization_name"],
            user_name=serializer.validated_data["name"],
            user_email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        create_email_verification(user)
        token_pair = issue_token_pair(user)
        response = api_success(
            data={
                "user": UserSerializer(user).data,
                "organization": {
                    "id": organization.id,
                    "name": organization.name,
                    "slug": organization.slug,
                    "domain": organization.primary_domain,
                },
                "access": token_pair["access"],
            },
            detail="Registration completed.",
            status_code=status.HTTP_201_CREATED,
        )
        response, refresh = apply_refresh_token_transport(request, response, token_pair["refresh"])
        if refresh:
            response.data["data"]["refresh"] = refresh
        return response


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token_pair = issue_token_pair(user)
        accesses = resolve_user_tenants(user)
        response = api_success(
            data={
                "user": UserSerializer(user).data,
                "access": token_pair["access"],
                "organizations": OrganizationAccessSerializer(accesses, many=True).data,
            },
            detail="Login successful.",
        )
        response, refresh = apply_refresh_token_transport(request, response, token_pair["refresh"])
        if refresh:
            response.data["data"]["refresh"] = refresh
        return response


class TokenObtainPairAPIView(LoginAPIView):
    pass


class TokenRefreshAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        input_serializer = TokenRefreshInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        refresh = input_serializer.validated_data.get("refresh") or request.COOKIES.get(
            "refresh_token"
        )
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)
        return api_success(data=serializer.validated_data, detail="Token refreshed.")


class TokenVerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        input_serializer = TokenVerifyInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        serializer = TokenVerifySerializer(data=input_serializer.validated_data)
        serializer.is_valid(raise_exception=True)
        return api_success(detail="Token is valid.")


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blacklist_user_tokens(request.user)
        response = api_success(detail="Logged out.")
        response.delete_cookie("refresh_token")
        return response


class VerifyEmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = VerifyEmailSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        verify_email_token(str(serializer.validated_data["token"]))
        return api_success(detail="Email verified.")

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify_email_token(str(serializer.validated_data["token"]))
        return api_success(detail="Email verified.")


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user:
            create_password_reset_token(user)
        return api_success(detail="If that account exists, a reset email has been sent.")


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_password(
            str(serializer.validated_data["token"]), serializer.validated_data["password"]
        )
        return api_success(detail="Password reset successful.")


class MeAPIView(APIView):
    permission_classes = [IsTenantAuthenticated]

    def get(self, request):
        payload = {
            "user": UserSerializer(request.user).data,
            "organization": {
                "id": request.tenant.id,
                "name": request.tenant.name,
                "slug": request.tenant.slug,
                "domain": request.tenant.primary_domain,
            },
            "role": request.membership.role,
        }
        return api_success(data=MeSerializer(payload).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(data=UserSerializer(request.user).data, detail="Profile updated.")


class MembersAPIView(APIView):
    permission_classes = [IsTenantAuthenticated]

    def get(self, request):
        members = Membership.objects.filter(is_active=True)
        return api_success(data=MemberSerializer(members, many=True).data)


class MemberDetailAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def patch(self, request, user_id: int):
        serializer = MemberRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = get_object_or_404(Membership, user_id=user_id, is_active=True)
        update_member_role(request.user, member, serializer.validated_data["role"])
        return api_success(data=MemberSerializer(member).data, detail="Member updated.")

    def delete(self, request, user_id: int):
        member = get_object_or_404(Membership, user_id=user_id, is_active=True)
        remove_member(request.user, member)
        return api_success(detail="Member removed.")


class InvitationsAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        invites = Invitation.objects.all()
        return api_success(data=InvitationSerializer(invites, many=True).data)

    def post(self, request):
        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite = invite_member(
            request.tenant,
            request.user,
            serializer.validated_data["email"],
            serializer.validated_data["role"],
        )
        return api_success(
            data=InvitationSerializer(invite).data, detail="Invitation created.", status_code=201
        )


class InvitationAcceptAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if getattr(request.tenant, "schema_name", "public") == "public":
            return Response(
                {
                    "data": None,
                    "detail": "Invitation acceptance must target a tenant domain or tenant header.",
                    "error": "tenant_required",
                },
                status=400,
            )
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        accepted_user = accept_invitation(
            request.tenant,
            serializer.validated_data["token"],
            user=user,
            name=serializer.validated_data.get("name"),
            password=serializer.validated_data.get("password"),
        )
        return api_success(data=UserSerializer(accepted_user).data, detail="Invitation accepted.")


class ProjectsAPIView(APIView):
    permission_classes = [IsTenantAuthenticated]

    def get(self, request):
        return api_success(data=ProjectSerializer(Project.objects.all(), many=True).data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = create_project(
            request.user,
            serializer.validated_data["name"],
            serializer.validated_data.get("description", ""),
        )
        return api_success(
            data=ProjectSerializer(project).data, detail="Project created.", status_code=201
        )


class ProjectDetailAPIView(APIView):
    permission_classes = [IsTenantAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Project, pk=pk)

    def get(self, request, pk):
        return api_success(data=ProjectSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        if request.membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            return Response(
                {"data": None, "detail": "Admin access required.", "error": "forbidden"}, status=403
            )
        project = self.get_object(pk)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(data=ProjectSerializer(project).data, detail="Project updated.")

    def delete(self, request, pk):
        if request.membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            return Response(
                {"data": None, "detail": "Admin access required.", "error": "forbidden"}, status=403
            )
        project = self.get_object(pk)
        project.delete()
        return api_success(detail="Project deleted.")


class AuditLogAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        return api_success(data=AuditLogSerializer(AuditLog.objects.all(), many=True).data)


class BillingOverviewAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        subscription = get_or_create_subscription(request.tenant)
        return api_success(data=SubscriptionSerializer(subscription).data)


class BillingCheckoutAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = create_checkout_session(request.tenant, serializer.validated_data["plan"])
        return api_success(data={"url": session["url"]}, detail="Checkout session created.")


class BillingPortalAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def post(self, request):
        session = create_customer_portal_session(request.tenant)
        return api_success(data={"url": session["url"]}, detail="Customer portal session created.")


class ApiKeysAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        keys = ApiKey.objects.filter(organization=request.tenant)
        return api_success(data=ApiKeySerializer(keys, many=True).data)

    def post(self, request):
        serializer = ApiKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key, raw_token = create_api_key(
            request.tenant, request.user, serializer.validated_data["name"]
        )
        payload = ApiKeySerializer(api_key).data
        payload["token"] = raw_token
        return api_success(data=payload, detail="API key created.", status_code=201)


class ApiKeyRevokeAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def post(self, request, pk):
        api_key = get_object_or_404(ApiKey, pk=pk, organization=request.tenant)
        revoke_api_key(api_key, request.user.id)
        return api_success(detail="API key revoked.")


class StripeWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body.decode("utf-8")
        if settings.STRIPE_WEBHOOK_SECRET:
            signature = request.headers.get("Stripe-Signature", "")
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
            event_payload = event.to_dict()
        else:
            event_payload = json.loads(payload or "{}")
        process_stripe_webhook_task.delay(event_payload)
        return api_success(detail="Webhook accepted.")
