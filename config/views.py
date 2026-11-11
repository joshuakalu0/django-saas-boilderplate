from django.db import connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    return JsonResponse({"status": "ok", "schema": connection.schema_name})
