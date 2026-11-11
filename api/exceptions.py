from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        message = exc.messages if hasattr(exc, "messages") else str(exc)
        return Response(
            {
                "data": None,
                "detail": message,
                "error": "validation_error",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data
        if isinstance(exc, ValidationError):
            detail = response.data
        return Response(
            {
                "data": None,
                "detail": detail,
                "error": getattr(exc, "default_code", "request_error"),
            },
            status=response.status_code,
        )
    return Response(
        {
            "data": None,
            "detail": "An unexpected error occurred.",
            "error": "server_error",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
