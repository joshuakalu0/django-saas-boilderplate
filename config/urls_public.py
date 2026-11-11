from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config import views

urlpatterns = [
    path("", include("accounts.urls_public")),
    path("api/", include("api.urls")),
    path("api/docs/", include("api.docs_urls")),
    path("health/live/", views.live, name="health-live"),
    path("health/ready/", views.ready, name="health-ready"),
    path(settings.DJANGO_ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
