from django.contrib import admin

from tenants.models import Domain, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "schema_name", "is_active", "created_at")
    search_fields = ("name", "slug", "schema_name")


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary", "created_at")
    search_fields = ("domain",)
