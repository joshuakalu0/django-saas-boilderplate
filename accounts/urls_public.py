from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("", views.PublicHomeView.as_view(), name="home"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("auth/password-reset/", views.PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "auth/password-reset/<uuid:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("auth/tenants/", views.TenantSelectView.as_view(), name="tenant-select"),
]
