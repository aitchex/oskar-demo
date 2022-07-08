from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _t


class UserManager(BaseUserManager):
    """
    Custom user model manager where phone number is the unique identifier
    for authentication instead of usernames.
    """

    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError(_t("The phone number must be set"))
        else:
            self.phone = phone
            user = self.model(phone=phone, **extra_fields)
            user.set_password(password)
            user.save()

        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_otp", True)
        extra_fields.setdefault("notify", True)
        extra_fields.setdefault("is_2fa", False)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_wholesaler", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault("is_otp", False)
        extra_fields.setdefault("notify", True)
        extra_fields.setdefault("is_2fa", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_wholesaler", False)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_t("Superuser must have is_staff=True"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_t("Superuser must have is_superuser=True"))

        return self._create_user(phone, password, **extra_fields)
