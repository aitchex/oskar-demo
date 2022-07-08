from itertools import chain
from json import dumps as json_dumps
from django.forms.models import model_to_dict
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.urls import reverse

from jdatetime import datetime as jdate

from utils.const import DELTA_TIME
from utils.product import (
    RATELIMIT_PARAMETERS,
    SORT_PARAMETERS,
    URL_PARAMETERS,
    ceil_max_price,
    filter_and_sort_products,
    get_offers,
    get_url_parameters,
    get_variations_images,
    get_variations_info_dict,
    trim_product_list,
)
from utils.user import is_user_wholesaler
from utils.decorator import cache_per_type, ratelimit_parameters

from shop.context_processors import categories
from shop.models import Product, ProductVariation
from category.models import Category, SubCategory, SubSubCategory
from variation.models import Brand, Color, Size

PRODUCT_COUNT = 24


@cache_per_type(timeout=120, prefix="home")
def home(request: HttpRequest, *args, **kwargs):
    suggestions = []
    is_wholesaler = kwargs.get("is_wholesaler", False) or is_user_wholesaler(request)

    sale_products = cache.get("products_sale") if not is_wholesaler else None

    sort_parameter = SORT_PARAMETERS["bestseller"]
    bestsellers = cache.get(
        f"products_sorted_{sort_parameter}" + ("_w" if is_wholesaler else "")
    )

    category: Category = (
        categories(None)["categories"][0]
        if len(categories(None)["categories"]) > 0
        else None
    )

    if category:
        for item in category.sub_categories()[:4]:
            products = []
            for product in Product.objects.filter(
                sub_category=item, is_active=True
            ).order_by("-created_on"):
                product: Product
                if (not is_wholesaler and product.is_available()) or (
                    is_wholesaler and product.is_available_wholesale()
                ):
                    products.append(product)
                    if len(products) >= 5:
                        break
            suggestions.append(
                {
                    "category": item,
                    "products": products,
                    "description": "",
                }
            )

    return render(
        request,
        "shop/home.html",
        {
            "is_wholesaler": is_wholesaler,
            "products": sale_products,
            "suggestions": suggestions,
            "bestsellers": bestsellers,
        },
    )


@cache_per_type(timeout=120, prefix="shop")
@ratelimit_parameters(key="ip", rate="3/3s", parameters=RATELIMIT_PARAMETERS)
def shop(
    request: HttpRequest,
    category=None,
    sub_category=None,
    sub_sub_category=None,
    *args,
    **kwargs,
):
    if getattr(request, "limited", False):
        response = render(
            request,
            "429.html",
            {"seconds": 4, "next": request.get_full_path()},
            status=429,
        )
        response["Retry-After"] = 4
        return response

    is_wholesaler = kwargs.get("is_wholesaler", False) or is_user_wholesaler(request)

    url_parameters = get_url_parameters(request)

    current_sort = "1"

    products = (
        Product.objects.filter(is_active=True).order_by("-created_on")
        if not url_parameters["search"]
        else Product.objects.filter(
            is_active=True,
            name__icontains=url_parameters["search"],
        ).order_by("-created_on")
    )

    if category:
        category = get_object_or_404(
            Category.objects,
            slug=category,
        )

    if sub_category:
        sub_category = get_object_or_404(
            SubCategory.objects,
            slug=sub_category,
            category=category,
        )

    if sub_sub_category:
        sub_sub_category = get_object_or_404(
            SubSubCategory.objects,
            slug=sub_sub_category,
            sub_category=sub_category,
        )

    if sub_sub_category:
        products = products.filter(sub_sub_category=sub_sub_category)
    elif sub_category:
        products = products.filter(sub_category=sub_category)
    elif category:
        products = products.filter(category=category)

    variations = ProductVariation.objects.filter(product__in=products)

    brands = Brand.objects.filter(
        id__in=products.values_list("brand__id", flat=True)
    ).order_by("name")

    colors = Color.objects.filter(
        id__in=set(
            chain(
                variations.values_list("color__id", flat=True),
                variations.values_list("color_2__id", flat=True),
                variations.values_list("color_3__id", flat=True),
            )
        )
    ).order_by("name")

    sizes = sorted(
        set(Size.objects.filter(id__in=variations.values_list("size__id", flat=True))),
        key=lambda s: (0, int(s.name)) if s.name.isdigit() else (1, s.name),
    )

    product_ids = products.values_list("id", flat=True)
    products = list(products)

    if kwargs.get("offers", False):
        if is_wholesaler:
            return redirect("products")
        products = get_offers(products)

    products = trim_product_list(products=products, wholesale=is_wholesaler)

    max_slider = ceil_max_price(products, 1000, is_wholesaler)

    products, current_sort = filter_and_sort_products(request, products, product_ids)

    paginator = Paginator(products, PRODUCT_COUNT)
    page = "1"
    try:
        page = request.GET.get("page")
        products = paginator.page(page)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    except:
        products = paginator.page(1)

    title = (
        sub_sub_category.name
        if sub_sub_category
        else (
            sub_category.name if sub_category else (category.name if category else None)
        )
    )

    return render(
        request,
        "shop/shop.html",
        {
            "is_wholesaler": is_wholesaler,
            "url_parameters": URL_PARAMETERS,
            "sort_parameters": SORT_PARAMETERS,
            "products": products,
            "brands": brands,
            "colors": colors,
            "sizes": sizes,
            "page": page,
            "min_slider": 0,
            "max_slider": max_slider if max_slider >= 10000 else 10000,
            "title": title,
            "current": {
                "url_parameters": url_parameters,
                "sort": current_sort,
                "category": category,
                "sub_category": sub_category,
                "sub_sub_category": sub_sub_category,
            },
        },
    )


@cache_per_type(timeout=120, prefix="product")
def product(request: HttpRequest, pid=None, slug=None, *args, **kwargs):
    if not pid:
        return redirect("products")

    is_wholesaler = kwargs.get("is_wholesaler", False) or is_user_wholesaler(request)

    product: Product = get_object_or_404(
        Product.objects.filter(is_active=True),
        pk=pid,
    )
    variation: ProductVariation = (
        product.get_lowest_price_variation_sorted()
        if not is_wholesaler
        else product.get_lowest_price_variation_wholesale_sorted()
    )
    variations = sorted(
        ProductVariation.objects.filter(is_active=True, product=product),
        key=lambda v: str([c.name for c in v.colors()]),
    )

    shamsi = jdate.fromgregorian(date=product.updated_on) + DELTA_TIME
    shamsi = shamsi.strftime("%Y/%m/%d")

    images = get_variations_images(product)
    info = get_variations_info_dict(product)

    sizes = sorted(
        set([v.size for v in variations if v.size]),
        key=lambda v: (0, int(v.name)) if v.name.isdigit() else (1, v.name),
    )

    colors = [
        dict(variation=v.id, colors=[model_to_dict(c) for c in v.colors()])
        for v in variations
        if len(v.colors()) > 0
    ]

    suggestions = []
    if product.sub_sub_category and len(suggestions) < 5:
        suggestions.extend(
            Product.objects.filter(sub_sub_category=product.sub_sub_category)
            .exclude(id__in=[s.id for s in suggestions] + [product.id])
            .order_by("-created_on")[:5]
        )
    if product.sub_category and len(suggestions) < 5:
        suggestions.extend(
            Product.objects.filter(sub_category=product.sub_category)
            .exclude(id__in=[s.id for s in suggestions] + [product.id])
            .order_by("-created_on")[:5]
        )
    if product.category and len(suggestions) < 5:
        suggestions.extend(
            Product.objects.filter(category=product.category)
            .exclude(id__in=[s.id for s in suggestions] + [product.id])
            .order_by("-created_on")[:5]
        )

    def modify_data(variation: ProductVariation):
        if not variation.is_sale():
            variation.sale_price = None
        if not is_wholesaler and not variation.is_available():
            variation.price = None
        elif is_wholesaler:
            variation.price = variation.wholesale_price
            variation.sale_price = None
            variation.sale_start = None
            variation.sale_end = None
            if not variation.is_available_wholesale():
                variation.price = None
        variation.original_price = None
        variation.wholesale_price = None

        variation = model_to_dict(variation)
        for key in (
            "color",
            "color_2",
            "color_3",
            "dimension_x",
            "dimension_y",
            "dimension_z",
            "other_variations",
            "product",
            "shipping_methods",
            "stock",
            "weight",
            "wholesale_price",
        ):
            del variation[key]

        return variation

    variations_dict = [modify_data(v) for v in variations]

    return render(
        request,
        "shop/product.html",
        {
            "is_wholesaler": is_wholesaler,
            "page_url": reverse("product", kwargs={"pid": pid, "slug": product.slug}),
            "product": product,
            "variation": variation,
            "variations": variations,
            "variations_json": json_dumps(variations_dict, default=str),
            "current": {
                "category": product.category,
                "sub_category": product.sub_category,
                "sub_sub_category": product.sub_sub_category,
            },
            "shamsi": shamsi,
            "images": images,
            "info": info[str(variation.id)] if variation else None,
            "info_json": json_dumps(info, default=str),
            "sizes": sizes,
            "colors": colors,
            "colors_json": json_dumps(colors, default=str),
            "suggestions": suggestions[:5],
        },
    )


def certificates(request: HttpRequest):
    return render(request, "shop/certificates.html")
