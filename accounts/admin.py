from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import EmailVerification, OrganizationAccess, PasswordResetToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "name", "is_active", "is_staff", "email_verified_at")
    ordering = ("email",)
    list_filter = ("is_active", "is_staff")
    search_fields = ("email", "name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("name", "avatar", "email_verified_at")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "password1", "password2"),
            },
        ),
    )


admin.site.register(OrganizationAccess)
admin.site.register(EmailVerification)
admin.site.register(PasswordResetToken)
