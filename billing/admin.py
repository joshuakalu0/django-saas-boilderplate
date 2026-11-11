from django.contrib import admin

from billing.models import ApiKey, Subscription

admin.site.register(Subscription)
admin.site.register(ApiKey)
