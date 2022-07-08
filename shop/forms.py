from django import forms

from cart_variation.models import Shipping
from shop.models import Image, Product, ProductVariation

from utils.const import BOOL_CHOICES


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            "is_active": forms.Select(choices=BOOL_CHOICES),
        }


class ProductVariationForm(forms.ModelForm):
    class Meta:
        model = ProductVariation
        fields = "__all__"
        widgets = {
            "is_active": forms.Select(choices=BOOL_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super(ProductVariationForm, self).__init__(*args, **kwargs)
        shipping_methods = self.fields["shipping_methods"]
        shipping_methods.initial = [sm.id for sm in Shipping.objects.all()]


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = "__all__"
        widgets = {
            "is_active": forms.Select(choices=BOOL_CHOICES),
        }
