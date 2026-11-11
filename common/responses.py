from rest_framework.response import Response


def api_success(data=None, detail="OK", status_code=200):
    return Response({"data": data, "detail": detail, "error": None}, status=status_code)


def api_error(detail, error="request_error", status_code=400, data=None):
    return Response({"data": data, "detail": detail, "error": error}, status=status_code)
