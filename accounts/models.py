import uuid
from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.constants import (
    EMAIL_VERIFICATION_EXPIRY_HOURS,
    PASSWORD_RESET_EXPIRY_HOURS,
    MembershipRole,
)
from common.models import TimeStampedModel


def email_verification_expiry():
    return timezone.now() + timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)


def password_reset_expiry():
    return timezone.now() + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    avatar = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None


class OrganizationAccess(TimeStampedModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="organization_accesses",
    )
    organization = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="user_accesses",
    )
    role = models.CharField(max_length=20, choices=MembershipRole.choices)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "organization")
        ordering = ["organization__name"]


class EmailVerification(TimeStampedModel):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="verifications"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField(default=email_verification_expiry)
    consumed_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_valid(self):
        return self.consumed_at is None and self.expires_at >= timezone.now()


class PasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField(default=password_reset_expiry)
    consumed_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_valid(self):
        return self.consumed_at is None and self.expires_at >= timezone.now()
