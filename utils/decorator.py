from functools import wraps
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.cache import get_cache_key
from django.views.decorators.cache import cache_page

from ratelimit.decorators import ratelimit

from utils.user import is_user_wholesaler


def cache_per_type(timeout: int, prefix: str = ""):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            def _get_key(req, wholesaler):
                return get_cache_key(
                    request=req,
                    key_prefix=prefix + ("_w" if wholesaler else ""),
                )

            cache_token = cache.get("cache_token")

            is_wholesaler = is_user_wholesaler(request)

            pid = request.resolver_match.kwargs.get("pid")
            if pid:
                path = request.path.split("/")
                if len(path) > 2 and path[1] == "product":
                    request.path = f"/product/{pid}/"

            if cache_token in [
                request.META.get("cache-token-u", "-1"),
                request.META.get("cache-token-w", "-1"),
            ]:
                is_wholesaler = "cache-token-w" in request.META.keys()
                cache_key = _get_key(request, is_wholesaler)

                if cache_key:
                    kwargs["is_wholesaler"] = is_wholesaler
                    view = view_func(request, *args, **kwargs)

                    header_key = cache_key.split(".")
                    header_key[3] = "cache_header"
                    header_key.pop(7)
                    header_key.pop(5)
                    header_key = ".".join(header_key)

                    cache.set(header_key, [], timeout)
                    cache.set(cache_key, view, timeout)
                    return HttpResponse("ok")

            cache_key = _get_key(request, is_wholesaler)
            kwargs["is_wholesaler"] = is_wholesaler
            view = view_func(request, *args, **kwargs) if not cache_key else None

            def _view_func(request, *args, **kwargs):
                return view if view else view_func(request, *args, **kwargs)

            if not view or view.status_code in [200, 304]:
                if is_user_wholesaler(request) or is_wholesaler:
                    return cache_page(timeout, key_prefix=f"{prefix}_w")(_view_func)(
                        request, *args, **kwargs
                    )
                else:
                    return cache_page(timeout, key_prefix=prefix)(_view_func)(
                        request, *args, **kwargs
                    )
            else:
                return view

        return _wrapped_view

    return decorator


def ratelimit_parameters(
    group=None,
    key=None,
    rate=None,
    method=["GET", "POST"],
    block=False,
    parameters=[],
):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            if len(parameters) > 0 and (
                (
                    request.method == "GET"
                    and set(parameters).intersection(request.GET.keys())
                )
                or (
                    request.method == "POST"
                    and set(parameters).intersection(request.POST.keys())
                )
            ):
                return ratelimit(group, key, rate, method, block)(view_func)(
                    request, *args, **kwargs
                )
            else:
                return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def cache_per_session(timeout: int, prefix: str = ""):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            session = request.session.session_key
            if not session:
                request.session.create()
                session = request.session.session_key
            return cache_page(timeout, key_prefix=f"{prefix}_{str(session)}")(
                view_func
            )(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def cache_cart(timeout: int, prefix: str = ""):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            from django.utils import timezone
            from cart.models import Cart

            session = request.session.session_key
            if not session:
                request.session.create()
                session = request.session.session_key

            try:
                cart: Cart = Cart.objects.get(session=session)
            except Cart.DoesNotExist:
                cart: Cart = Cart.objects.create(session=session)
                cart.save()

            update_time_as_seconds = (
                cart.updated_on.replace(tzinfo=None) - timezone.datetime(1970, 1, 1)
            ).total_seconds()

            return cache_page(
                timeout,
                key_prefix=f"{prefix}_{str(cart.id)}_{str(update_time_as_seconds)}",
            )(view_func)(request, *args, **kwargs)

        return _wrapped_view

    return decorator
