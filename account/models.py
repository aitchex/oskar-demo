from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _t

from account.managers import UserManager
from cart_variation.models import Province
from utils.const import CHAR_MAX_LENGTH

PHONE_REGEX = RegexValidator(
    regex=r"^9\d{9}$",
    message="Phone number must be entered in the following format: '9123456789'. Up to 10 digits allowed.",
)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(
        _t("phone number"),
        validators=[PHONE_REGEX],
        max_length=20,
        unique=True,
    )

    username = models.CharField(max_length=CHAR_MAX_LENGTH, null=True, blank=True)

    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)

    notify = models.BooleanField(default=True)

    is_otp = models.BooleanField(default=True)
    is_2fa = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_wholesaler = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    otp_password = models.CharField(max_length=200, null=True, blank=True)
    otp_expire = models.DateTimeField(default=timezone.now)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.phone

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    name = models.CharField(max_length=200, default="Address")

    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True)
    city = models.CharField(max_length=200)
    address = models.TextField()
    postal_code = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, validators=[PHONE_REGEX])
    mobile_phone_number = models.CharField(max_length=200)

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.name}"
