from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler to return unified JSON error responses across the API.
    """
    response = exception_handler(exc, context)

    if response is not None:
        message = "An error occurred."
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = str(response.data['detail'])
            else:
                try:
                    first_key = next(iter(response.data))
                    val = response.data[first_key]
                    if isinstance(val, list) and len(val) > 0:
                        message = f"{first_key}: {val[0]}"
                    else:
                        message = f"{first_key}: {val}"
                except StopIteration:
                    pass
        elif isinstance(response.data, list) and len(response.data) > 0:
            message = str(response.data[0])

        response.data = {
            "success": False,
            "status_code": response.status_code,
            "message": message,
            "errors": response.data,
        }

    return response
