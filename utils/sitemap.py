from django.contrib import sitemaps as _sitemaps
from django.urls import reverse

from category.models import Category, SubCategory, SubSubCategory
from shop.models import Product


def sitemaps() -> dict:
    return {
        "static": StaticViewSitemap,
        "category": CategorySitemap,
        "sub_category": SubCategorySitemap,
        "sub_sub_category": SubSubCategorySitemap,
        "product": ProductSitemap,
    }


class StaticViewSitemap(_sitemaps.Sitemap):
    priority = 0.5
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return [
            "home",
            "products",
            "cart",
            "checkout",
            "login",
            "profile",
            "certificates",
        ]

    def location(self, item: str):
        return reverse(item)


class CategorySitemap(_sitemaps.Sitemap):
    priority = 0.6
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return Category.objects.all()

    def location(self, obj: Category):
        return reverse(
            "products",
            kwargs={
                "category": obj.slug,
            },
        )


class SubCategorySitemap(_sitemaps.Sitemap):
    priority = 0.6
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return SubCategory.objects.all()

    def location(self, obj: SubCategory):
        return reverse(
            "products",
            kwargs={
                "category": obj.category.slug,
                "sub_category": obj.slug,
            },
        )


class SubSubCategorySitemap(_sitemaps.Sitemap):
    priority = 0.6
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return SubSubCategory.objects.all()

    def location(self, obj: SubSubCategory):
        return reverse(
            "products",
            kwargs={
                "category": obj.sub_category.category.slug,
                "sub_category": obj.sub_category.slug,
                "sub_sub_category": obj.slug,
            },
        )


class ProductSitemap(_sitemaps.Sitemap):
    priority = 0.9
    changefreq = "daily"
    protocol = "https"

    def items(self):
        return Product.objects.filter(is_active=True).order_by("created_on")

    def location(self, obj: Product):
        return reverse(
            "product",
            kwargs={
                "pid": obj.id,
                "slug": obj.slug,
            },
        )

    def lastmod(self, obj: Product):
        return obj.updated_on
