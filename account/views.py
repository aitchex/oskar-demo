from django.contrib.auth import get_user_model, logout as logout_user
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import EmptyPage, Paginator
from django.urls import reverse

from jdatetime import datetime as jdate
from ratelimit.decorators import ratelimit

from account.forms import OTPAuthForm

from cart.models import Order, OrderItem
from utils.const import DELTA_TIME
from utils.otp import login_otp, request_otp
from utils.cart import get_cart_or_none


@ratelimit(key="ip", rate="6/m", method=["POST"])
@ratelimit(key="ip", rate="100/d", method=["POST"])
def login(request: HttpRequest):
    is_limited = getattr(request, "limited", False)

    if request.user.is_authenticated:
        return redirect("profile")

    auth_form = OTPAuthForm()

    if request.method == "POST":
        auth_form = OTPAuthForm(request.POST)
        response: dict = {"message": "", "type": ""}

        if is_limited:
            response = {"message": "ratelimited", "type": "error"}
        elif auth_form.is_valid():
            if auth_form.cleaned_data.get("password"):
                cart = get_cart_or_none(request)
                phone = auth_form.cleaned_data.get("phone")
                password = auth_form.cleaned_data.get("password")

                if login_otp(request, phone, password):
                    if cart:
                        cart.user = get_user_model().objects.get(phone=phone)
                        cart.save()

                    response = {
                        "message": "login_ok",
                        "type": "redirect",
                        "url": reverse("profile"),
                    }
                else:
                    response = {"message": "login_failed", "type": "error"}

            elif auth_form.cleaned_data.get("phone"):
                phone = auth_form.cleaned_data.get("phone")
                user = get_user_model().objects.filter(phone=phone).exists()

                if request_otp(phone):
                    if user:
                        response = {"message": "otp_sent", "type": "login"}
                    else:
                        response = {"message": "otp_sent", "type": "signup"}
                else:
                    response = {"message": "otp_failed", "type": "error"}
        else:
            response = {"message": "form_is_not_valid", "type": "error"}

        return JsonResponse(response)

    return render(
        request,
        "account/otp-login.html",
        {"auth_form": auth_form},
    )


def logout(request: HttpRequest):
    logout_user(request)
    return redirect("home")


@login_required(login_url="login")
@ratelimit(key="ip", rate="4/s")
@ratelimit(key="ip", rate="6/3s")
@ratelimit(key="ip", rate="12/9s")
def profile(request: HttpRequest):
    if getattr(request, "limited", False):
        response = render(
            request,
            "429.html",
            {"seconds": 4, "next": request.get_full_path()},
            status=429,
        )
        response["Retry-After"] = 4
        return response

    # if request.user.is_superuser:
    #     return redirect("admin:index")

    phone = request.user.phone

    orders = (
        Order.objects.filter(user=request.user)
        .exclude(status=-3)
        .order_by("-created_on")
    )

    for order in orders:
        shamsi = jdate.fromgregorian(date=order.created_on) + DELTA_TIME
        order.created_on = shamsi.strftime("%Y/%m/%d")

    return render(
        request,
        "account/profile.html",
        {
            "phone": phone,
            "orders": orders,
        },
    )


@login_required(login_url="login")
@ratelimit(key="ip", rate="4/s")
@ratelimit(key="ip", rate="6/3s")
@ratelimit(key="ip", rate="12/9s")
def orders(request: HttpRequest):
    if getattr(request, "limited", False):
        response = render(
            request,
            "429.html",
            {"seconds": 4, "next": request.get_full_path()},
            status=429,
        )
        response["Retry-After"] = 4
        return response

    # if request.user.is_superuser:
    #     return redirect("admin:index")

    orders = (
        Order.objects.filter(user=request.user)
        .exclude(status=-3)
        .order_by("-created_on")
    )

    paginator = Paginator(orders, 20)
    page = "1"
    try:
        page = request.GET.get("page")
        orders = paginator.page(page)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    except:
        orders = paginator.page(1)

    for order in orders:
        shamsi = jdate.fromgregorian(date=order.created_on) + DELTA_TIME
        order.created_on = shamsi.strftime("%Y/%m/%d")

    return render(
        request,
        "account/orders.html",
        {
            "orders": orders,
        },
    )


@login_required(login_url="login")
@ratelimit(key="ip", rate="4/s")
@ratelimit(key="ip", rate="6/3s")
@ratelimit(key="ip", rate="12/9s")
def order(request: HttpRequest, order_code: str):
    if getattr(request, "limited", False):
        response = render(
            request,
            "429.html",
            {"seconds": 4, "next": request.get_full_path()},
            status=429,
        )
        response["Retry-After"] = 4
        return response

    order = get_object_or_404(Order.objects, order_code=order_code)
    order_items = OrderItem.objects.filter(order=order)

    tracking_url = None
    if order.tracking_code and order.shipping_method.tracking_url:
        tracking_url = (
            "https://" + order.shipping_method.tracking_url + order.tracking_code
        )

    if request.user == order.user or request.user.is_superuser:
        return render(
            request,
            "account/order.html",
            {
                "order": order,
                "order_items": order_items,
                "tracking_url": tracking_url,
            },
        )
    else:
        raise PermissionDenied()


@login_required(login_url="login")
def invoice(request: HttpRequest, order_code: str):
    order = get_object_or_404(Order.objects, order_code=order_code)
    order_items = (
        OrderItem.objects.filter(order=order)
        .annotate(ordered_size=Cast("variation__size__name", IntegerField()))
        .order_by(
            "variation__product__name",
            "ordered_size",
            "variation__size__name",
            "variation__color__name",
            "variation__color_2__name",
            "variation__color_3__name",
        )
    )

    shamsi = jdate.fromgregorian(date=order.created_on) + DELTA_TIME
    order.created_on = shamsi.strftime("%Y/%m/%d")

    if request.user.is_superuser:
        return render(
            request,
            "account/invoice.html",
            {
                "order": order,
                "order_items": order_items,
            },
        )
    else:
        raise PermissionDenied()


@login_required(login_url="login")
def addresses(request: HttpRequest):
    return render(request, "account/addresses.html")


@login_required(login_url="login")
def address(request: HttpRequest):
    return render(request, "account/address.html")


@login_required(login_url="login")
def comments(request: HttpRequest):
    return render(request, "account/comments.html")
