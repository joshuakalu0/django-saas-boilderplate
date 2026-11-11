from django.core.management.base import BaseCommand

from tenants.services import ensure_public_tenant


class Command(BaseCommand):
    help = "Create or update the public tenant and its primary domain."

    def handle(self, *args, **options):
        tenant, created = ensure_public_tenant()
        action = "Created" if created else "Verified"
        self.stdout.write(self.style.SUCCESS(f"{action} public tenant: {tenant.schema_name}"))
