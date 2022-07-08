from django.http.request import HttpRequest


def get_session_key(request: HttpRequest):
    session = request.session.session_key
    if not session:
        session = request.session.create()
    return session


def get_ip(request: HttpRequest):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
