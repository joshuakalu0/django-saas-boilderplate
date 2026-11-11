from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
]
