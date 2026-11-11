from django.contrib import admin

from workspace.models import AuditLog, Invitation, Membership, Project

admin.site.register(Membership)
admin.site.register(Project)
admin.site.register(Invitation)
admin.site.register(AuditLog)
