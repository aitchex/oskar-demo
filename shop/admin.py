from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from nested_admin import NestedModelAdmin, NestedStackedInline

from shop.forms import ImageForm, ProductForm, ProductVariationForm
from shop.models import FishingReel, FishingRod, Product, Image, ProductVariation


class FishingRodInline(NestedStackedInline):
    model = FishingRod
    extra = 0
    max_num = 1


class FishingReelInline(NestedStackedInline):
    model = FishingReel
    extra = 0
    max_num = 1

    autocomplete_fields = [
        "suitable_for",
        "clutch",
    ]


class ImageInline(NestedStackedInline):
    model = Image
    form = ImageForm
    extra = 0


@admin.register(ProductVariation)
class ProductVariationAdmin(NestedModelAdmin):
    form = ProductVariationForm
    inlines = [FishingRodInline, FishingReelInline, ImageInline]

    list_display = [
        "size",
        "colors_list",
        "price",
        "wholesale_price",
        "sale_price",
        "original_price",
        "stock",
        "is_active",
    ]

    list_display_links = ["size", "colors_list"]

    list_editable = [
        "price",
        "wholesale_price",
        "sale_price",
        "original_price",
        "stock",
        "is_active",
    ]

    sortable_by = []

    autocomplete_fields = [
        "product",
        "color",
        "color_2",
        "color_3",
        "size",
    ]

    search_fields = [
        "id",
        "product__name",
        "size__name",
        "color__name",
        "color_2__name",
        "color_3__name",
    ]

    @admin.display(description="Color")
    def colors_list(self, obj):
        colors = list(map(str, obj.colors()))

        if colors:
            return " - ".join(colors)
        else:
            return "-"

    def has_module_permission(self, request):
        return False


class ProductVariationInline(NestedStackedInline):
    model = ProductVariation
    form = ProductVariationForm
    inlines = [FishingRodInline, FishingReelInline, ImageInline]
    extra = 0

    autocomplete_fields = [
        "color",
        "color_2",
        "color_3",
        "size",
    ]


@admin.register(Product)
class ProductAdmin(NestedModelAdmin):
    form = ProductForm
    inlines = [ProductVariationInline]

    search_fields = ["name"]

    list_display = [
        "name",
        "variations_list",
        "is_active",
        "created_on",
        "link_list",
    ]

    prepopulated_fields = {"slug": ("name",)}

    autocomplete_fields = [
        "brand",
        "category",
        "sub_category",
        "sub_sub_category",
    ]

    @admin.display(description="Variations")
    def variations_list(self, obj):
        variations = ProductVariation.objects.filter(product=obj)
        count = variations.count()

        if count == 0:
            return "0 Variation"

        url = (
            reverse("admin:shop_productvariation_changelist")
            + "?"
            + urlencode({"product__id": f"{obj.id}"})
        )

        return format_html(
            '<a href="{}">{} Variation{}</a>', url, count, "s" if count > 1 else ""
        )

    @admin.display(description="Link")
    def link_list(self, obj):
        url = reverse("product", kwargs={"pid": obj.id, "slug": obj.slug})

        return format_html("<a target='_blank' href='{}'>View</a>", url)
