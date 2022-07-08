from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from cart_variation.models import Shipping
from category.models import Category, SubCategory, SubSubCategory
from utils.model import generate_thumbnail
from variation.models import Brand, Clutch, Color, Size, Suitable

from utils.const import (
    CHAR_MAX_LENGTH,
    IMAGE_PATH,
    IMAGE_WEBP_PATH,
    ORIGINAL_IMAGE_PATH,
    PRICE_REGEX,
    THUMBNAIL_PATH,
    THUMBNAIL_WEBP_PATH,
)


class Product(models.Model):
    name = models.CharField(
        max_length=CHAR_MAX_LENGTH,
    )
    slug = models.SlugField(
        max_length=CHAR_MAX_LENGTH,
        unique=True,
        allow_unicode=True,
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    material = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sub_sub_category = models.ForeignKey(
        SubSubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    limit = models.IntegerField(
        default=10,
    )
    wholesale_min_limit = models.IntegerField(
        default=3,
    )
    wholesale_max_limit = models.IntegerField(
        default=50,
    )

    short_description = models.TextField(
        null=True,
        blank=True,
    )
    description = models.TextField(
        null=True,
        blank=True,
    )

    alt = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    original_image = models.ImageField(
        upload_to=ORIGINAL_IMAGE_PATH,
        null=True,
        blank=True,
        verbose_name="product image",
    )
    image = models.ImageField(
        upload_to=IMAGE_PATH,
        null=True,
        blank=True,
        editable=False,
    )
    image_webp = models.ImageField(
        upload_to=IMAGE_WEBP_PATH,
        null=True,
        blank=True,
        editable=False,
    )
    thumbnail = models.ImageField(
        upload_to=THUMBNAIL_PATH,
        null=True,
        blank=True,
        editable=False,
    )
    thumbnail_webp = models.ImageField(
        upload_to=THUMBNAIL_WEBP_PATH,
        null=True,
        blank=True,
        editable=False,
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        self.prev_original_image = self.original_image

    def get_lowest_price_variation_wholesale(self):
        variations = ProductVariation.objects.filter(
            product=self,
            is_active=True,
            wholesale_price__isnull=False,
            stock__gt=0,
            stock__gte=self.wholesale_min_limit,
        )

        prices = sorted(variations, key=lambda v: int(v.wholesale_price))

        return prices[0] if len(prices) > 0 else None

    def get_lowest_price_variation_wholesale_sorted(self):
        variations = ProductVariation.objects.filter(
            product=self,
            is_active=True,
            wholesale_price__isnull=False,
            stock__gt=0,
            stock__gte=self.wholesale_min_limit,
        ).values("id", "wholesale_price", "size", "size__name")

        prices = sorted(
            variations,
            key=lambda v: (int(v.get("wholesale_price")), 0, int(v.get("size__name")))
            if v.get("size") and v.get("size__name").isdigit()
            else (int(v.get("wholesale_price")), 1, str(v.get("size"))),
        )

        return (
            ProductVariation.objects.get(id=prices[0]["id"])
            if len(prices) > 0
            else None
        )

    def get_lowest_price_wholesale(self) -> str:
        variation = self.get_lowest_price_variation_wholesale()
        return "" if not variation else variation.wholesale_price

    def get_lowest_price_variation(self):
        variations = ProductVariation.objects.filter(
            product=self,
            is_active=True,
            price__isnull=False,
            stock__gt=0,
        )

        prices = sorted(
            variations,
            key=lambda v: int(v.price),
        )

        if len(prices) > 0:
            sale_prices = sorted(
                [v for v in variations if v.sale_price],
                key=lambda v: int(v.sale_price),
            )
            if len(sale_prices) > 0 and sale_prices[0].sale_price:
                return (
                    prices[0]
                    if int(prices[0].price) < int(sale_prices[0].sale_price)
                    else sale_prices[0]
                )
            return prices[0]
        return None

    def get_lowest_price_variation_sorted(self):
        variations = ProductVariation.objects.filter(
            product=self,
            is_active=True,
            price__isnull=False,
            stock__gt=0,
        ).values("id", "price", "sale_price", "size", "size__name")

        prices = sorted(
            variations,
            key=lambda v: (int(v.get("price")), 0, int(v.get("size__name")))
            if v.get("size") and v.get("size__name").isdigit()
            else (int(v.get("price")), 1, str(v.get("size__name"))),
        )

        if len(prices) > 0:
            sale_prices = sorted(
                [v for v in variations if v.get("sale_price")],
                key=lambda v: (int(v.get("sale_price")), 0, int(v.get("size__name")))
                if v.get("size") and v.get("size__name").isdigit()
                else (int(v.get("sale_price")), 1, str(v.get("size__name"))),
            )
            if len(sale_prices) > 0 and sale_prices[0].get("sale_price"):
                return (
                    ProductVariation.objects.get(id=prices[0]["id"])
                    if int(prices[0]["price"]) < int(sale_prices[0]["sale_price"])
                    else ProductVariation.objects.get(id=sale_prices[0]["id"])
                )
            return ProductVariation.objects.get(id=prices[0]["id"])
        return None

    def get_lowest_price(self) -> str:
        variation = self.get_lowest_price_variation()
        return "" if not variation else variation.price

    # * Returns "sale_price" if there is a sale and "price" if there is not.
    def get_real_lowest_price(self) -> str:
        variation = self.get_lowest_price_variation()
        if variation:
            if variation.is_sale():
                return variation.sale_price
            else:
                return variation.price
        return ""

    def is_available(self) -> bool:
        variations = ProductVariation.objects.filter(
            product=self,
            is_active=True,
            price__isnull=False,
            stock__gt=0,
        )
        return self.is_active and variations.exists()

    def is_available_wholesale(self) -> bool:
        variations = ProductVariation.objects.filter(
            product=self,
            is_active=True,
            wholesale_price__isnull=False,
            stock__gt=0,
            stock__gte=self.wholesale_min_limit,
        )
        return self.is_active and variations.exists()

    def clean(self):
        if self.wholesale_min_limit > self.wholesale_max_limit:
            raise ValidationError(
                {
                    "wholesale_min_limit": [
                        "Wholesale min limit can't be greater than Wholesale max limit"
                    ],
                    "wholesale_max_limit": [
                        "Wholesale max limit can't be less than Wholesale min limit"
                    ],
                },
            )

    def save(self, *args, **kwargs):
        if self.sub_sub_category:
            self.sub_category = self.sub_sub_category.sub_category
            self.category = self.sub_category.category
        elif self.sub_category:
            self.category = self.sub_category.category

        if self.prev_original_image != self.original_image:
            generate_thumbnail(self)

        if (
            self.original_image
            and not self.image
            and not self.image_webp
            and not self.thumbnail
            and not self.thumbnail_webp
        ):
            self.alt = None
            self.original_image = None

        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ProductVariation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )

    price = models.CharField(
        max_length=20,
        validators=[PRICE_REGEX],
        help_text="toman",
    )
    wholesale_price = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[PRICE_REGEX],
        help_text="toman",
    )
    sale_price = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[PRICE_REGEX],
        help_text="toman",
    )
    original_price = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[PRICE_REGEX],
        help_text="toman",
    )

    sale_start = models.DateTimeField(
        null=True,
        blank=True,
    )
    sale_end = models.DateTimeField(
        null=True,
        blank=True,
    )

    stock = models.IntegerField(
        default=1,
        help_text="quantity",
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    weight = models.IntegerField(
        help_text="grams",
    )

    color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    color_2 = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="color_2",
    )
    color_3 = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="color_3",
    )

    dimension_x = models.FloatField(
        null=True,
        blank=True,
        help_text="centimeters",
    )
    dimension_y = models.FloatField(
        null=True,
        blank=True,
        help_text="centimeters",
    )
    dimension_z = models.FloatField(
        null=True,
        blank=True,
        help_text="centimeters",
    )

    other_variations = models.TextField(
        null=True,
        blank=True,
        help_text="separate variations using enter",
    )
    shipping_methods = models.ManyToManyField(
        Shipping,
        blank=False,
    )

    is_active = models.BooleanField(default=True)

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super(ProductVariation, self).__init__(*args, **kwargs)
        self.prev_sale_price = self.sale_price

    def is_available(self) -> bool:
        return (
            self.is_active and self.product.is_active and self.price and self.stock > 0
        )

    def is_available_wholesale(self) -> bool:
        return (
            self.is_active
            and self.product.is_active
            and self.wholesale_price
            and self.stock > 0
            and self.stock >= self.product.wholesale_min_limit
        )

    def is_sale(self) -> bool:
        check = False
        if self.sale_price:
            check = True
            if self.sale_end:
                check = timezone.now() < self.sale_end
            if self.sale_start:
                check = timezone.now() >= self.sale_start
            if (
                self.sale_start
                and self.sale_end
                and (
                    self.sale_end <= self.sale_start or timezone.now() >= self.sale_end
                )
            ):
                check = False
        return check

    def sale_remaining(self) -> int:
        if self.is_sale() and self.sale_end:
            return int((self.sale_end - timezone.now()).total_seconds())
        else:
            return -1

    def discount(self) -> str:
        return self.sale_price if self.is_sale() else None

    def colors(self) -> list:
        all_colors = []
        if self.color:
            all_colors.append(self.color)
            if self.color_2:
                all_colors.append(self.color_2)
                if self.color_3:
                    all_colors.append(self.color_3)
        return all_colors

    def dimensions(self) -> list:
        dims = []
        if self.dimension_x and self.dimension_x > 0:
            dims.append(self.dimension_x)
        if self.dimension_y and self.dimension_y > 0:
            dims.append(self.dimension_y)
        if self.dimension_z and self.dimension_z > 0:
            dims.append(self.dimension_z)
        return dims

    def clean(self):
        if (
            self.sale_price
            and self.price
            and self.sale_price.isdigit()
            and self.price.isdigit()
            and int(self.sale_price) >= int(self.price)
        ):
            raise ValidationError(
                {"sale_price": ["Sale price must be less than price"]}
            )

    def save(self, *args, **kwargs):
        if (
            self.prev_sale_price
            and self.sale_price
            and self.sale_start
            and self.sale_end
            and self.prev_sale_price != self.sale_price
            and timezone.now() > self.sale_end
        ):
            self.sale_start = None
            self.sale_end = None

        super(ProductVariation, self).save(*args, **kwargs)
        self.product.updated_on = datetime.now()
        self.product.save()

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Variation"
        verbose_name_plural = "Variations"

    def __str__(self) -> str:
        num = self.id if self.id else self.product.id
        size = (
            str(self.size)
            if self.size
            else "-".join([f"{d:g}" for d in self.dimensions()])
        )
        size = (" | " if size else "") + size

        color = "-".join([c.name for c in self.colors()])
        color = (" | " if color else "") + color

        return f"#{num}: {self.product.name} {size} {color}"


class Image(models.Model):
    variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
    )

    alt = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    original_image = models.ImageField(
        upload_to=ORIGINAL_IMAGE_PATH,
        verbose_name="product image",
    )
    image = models.ImageField(
        upload_to=IMAGE_PATH,
        null=True,
        blank=True,
        editable=False,
    )
    image_webp = models.ImageField(
        upload_to=IMAGE_WEBP_PATH,
        null=True,
        blank=True,
        editable=False,
    )
    thumbnail = models.ImageField(
        upload_to=THUMBNAIL_PATH,
        null=True,
        blank=True,
        editable=False,
    )
    thumbnail_webp = models.ImageField(
        upload_to=THUMBNAIL_WEBP_PATH,
        null=True,
        blank=True,
        editable=False,
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def save(self, *args, **kwargs):
        generate_thumbnail(self)

        if (
            self.original_image
            and self.image
            and self.image_webp
            and self.thumbnail
            and self.thumbnail_webp
        ):
            super(Image, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.alt if self.alt else self.variation.product.name


class FishingReel(models.Model):
    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
    )

    spool_material = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )
    suitable_for = models.ForeignKey(
        Suitable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    clutch = models.ForeignKey(
        Clutch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    bearings_qty = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )
    rotation_ratio = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )
    string_capacity = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]


class FishingRod(models.Model):
    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
    )

    length = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
        help_text="centimeters",
    )
    closed_length = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
        help_text="centimeters",
    )
    handle_length = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
        help_text="centimeters",
    )

    handle_material = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )
    rod_material = models.CharField(
        max_length=CHAR_MAX_LENGTH,
        null=True,
        blank=True,
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]
