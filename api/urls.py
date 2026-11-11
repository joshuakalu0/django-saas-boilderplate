from django.urls import path

from api import views

app_name = "api"

urlpatterns = [
    path("v1/auth/register/", views.RegisterAPIView.as_view(), name="register"),
    path("v1/auth/login/", views.LoginAPIView.as_view(), name="login"),
    path("v1/auth/token/", views.TokenObtainPairAPIView.as_view(), name="token-obtain"),
    path("v1/auth/token/refresh/", views.TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("v1/auth/token/verify/", views.TokenVerifyAPIView.as_view(), name="token-verify"),
    path("v1/auth/logout/", views.LogoutAPIView.as_view(), name="logout"),
    path("v1/auth/verify-email/", views.VerifyEmailAPIView.as_view(), name="verify-email"),
    path(
        "v1/auth/password-reset/",
        views.PasswordResetRequestAPIView.as_view(),
        name="password-reset",
    ),
    path(
        "v1/auth/password-reset/confirm/",
        views.PasswordResetConfirmAPIView.as_view(),
        name="password-reset-confirm",
    ),
    path("v1/me/", views.MeAPIView.as_view(), name="me"),
    path("v1/members/", views.MembersAPIView.as_view(), name="members"),
    path("v1/members/<int:user_id>/", views.MemberDetailAPIView.as_view(), name="member-detail"),
    path("v1/invitations/", views.InvitationsAPIView.as_view(), name="invitations"),
    path(
        "v1/invitations/accept/", views.InvitationAcceptAPIView.as_view(), name="invitation-accept"
    ),
    path("v1/projects/", views.ProjectsAPIView.as_view(), name="projects"),
    path("v1/projects/<uuid:pk>/", views.ProjectDetailAPIView.as_view(), name="project-detail"),
    path("v1/audit-log/", views.AuditLogAPIView.as_view(), name="audit-log"),
    path("v1/billing/", views.BillingOverviewAPIView.as_view(), name="billing-overview"),
    path("v1/billing/checkout/", views.BillingCheckoutAPIView.as_view(), name="billing-checkout"),
    path("v1/billing/portal/", views.BillingPortalAPIView.as_view(), name="billing-portal"),
    path("v1/api-keys/", views.ApiKeysAPIView.as_view(), name="api-keys"),
    path(
        "v1/api-keys/<int:pk>/revoke/", views.ApiKeyRevokeAPIView.as_view(), name="api-key-revoke"
    ),
    path("webhooks/stripe/", views.StripeWebhookAPIView.as_view(), name="stripe-webhook"),
]
