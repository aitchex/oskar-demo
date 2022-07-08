from django.urls import path

from account import views

urlpatterns = [
    path("", views.profile, name="profile"),
    path("orders/", views.orders, name="orders"),
    path("order/<str:order_code>/", views.order, name="order"),
    path("order/<str:order_code>/invoice/", views.invoice, name="invoice"),
    path("addresses/", views.addresses, name="addresses"),
    path("address/", views.address, name="address"),
    path("comments/", views.comments, name="comments"),
]
