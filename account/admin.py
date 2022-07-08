from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from account.forms import UserCreationForm, UserChangeForm
from account.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = [
        "phone",
        "notify",
        "is_wholesaler",
        "is_active",
    ]

    list_filter = []

    # Other fields: "password1", "password2", "is_otp", "is_2fa", "is_staff"
    fieldsets = [
        (None, {"fields": ("phone", "notify", "is_wholesaler", "is_active")}),
    ]
    add_fieldsets = [
        (None, {"fields": ("phone", "notify", "is_wholesaler", "is_active")}),
    ]

    search_fields = ["phone"]
    ordering = ["-date_joined"]
