from django.urls import path

from shop import views

urlpatterns = [
    path("", views.home, name="home"),
    path("certificates/", views.certificates, name="certificates"),
    path("products/", views.shop, name="search"),
    path("products/", views.shop, name="products"),
    path("products/offers/", views.shop, name="offers", kwargs={"offers": True}),
    path("products/<slug:category>/", views.shop, name="products"),
    path("products/<slug:category>/<slug:sub_category>/", views.shop, name="products"),
    path(
        "products/<slug:category>/<slug:sub_category>/<slug:sub_sub_category>/",
        views.shop,
        name="products",
    ),
    path("product/", views.product, name="product"),
    path("product/<int:pid>/", views.product, name="product"),
    path("product/<int:pid>/<str:slug>/", views.product, name="product"),
]
