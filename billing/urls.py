from django.urls import path

from billing import views

app_name = "billing"

urlpatterns = [
    path("", views.BillingOverviewView.as_view(), name="overview"),
    path("portal/", views.CustomerPortalView.as_view(), name="portal"),
    path("api-keys/create/", views.ApiKeyCreateView.as_view(), name="api-key-create"),
    path("api-keys/<int:key_id>/revoke/", views.ApiKeyRevokeView.as_view(), name="api-key-revoke"),
    path("success/", views.BillingSuccessView.as_view(), name="success"),
]
