from django.http.request import HttpRequest

from utils.user import is_user_active, is_user_wholesaler


def permissions(request: HttpRequest):
    return {
        "is_user_authenticated": request.user.is_authenticated,
        "is_user_wholesaler": is_user_wholesaler(request),
        "is_user_active": is_user_active(request),
    }
