from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from account.models import User, PHONE_REGEX

from utils.const import BOOL_CHOICES, CHAR_MAX_LENGTH
from utils.otp import OTP_DIGITS


class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["phone"]
        widgets = {
            "notify": forms.Select(choices=BOOL_CHOICES),
            "is_wholesaler": forms.Select(choices=BOOL_CHOICES),
            "is_active": forms.Select(choices=BOOL_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields["password1"].required = False
        self.fields["password2"].required = False


class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["phone"]
        widgets = {
            "notify": forms.Select(choices=BOOL_CHOICES),
            "is_wholesaler": forms.Select(choices=BOOL_CHOICES),
            "is_active": forms.Select(choices=BOOL_CHOICES),
        }


class UserLoginForm(forms.Form):
    phone = forms.CharField(max_length=10, required=True)
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput,
        required=True,
    )


class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=CHAR_MAX_LENGTH, required=True)
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput,
        required=False,
    )
    otp = forms.CharField(max_length=OTP_DIGITS, required=False)


class OTPAuthForm(forms.Form):
    phone = forms.CharField(
        validators=[PHONE_REGEX],
        max_length=20,
        required=True,
    )
    password = forms.CharField(max_length=OTP_DIGITS, required=False)
