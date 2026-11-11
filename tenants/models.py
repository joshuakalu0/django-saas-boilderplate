from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from common.models import TimeStampedModel


class Organization(TenantMixin, TimeStampedModel):
    auto_create_schema = True
    auto_drop_schema = False

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def primary_domain(self):
        primary = self.domains.filter(is_primary=True).first()
        return primary.domain if primary else None


class Domain(DomainMixin, TimeStampedModel):
    class Meta:
        ordering = ["domain"]

    def __str__(self):
        return self.domain
