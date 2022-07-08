from django.core.validators import RegexValidator
from jdatetime import timedelta

DELTA_TIME = timedelta(hours=3, minutes=30)

CHAR_MAX_LENGTH = 200

ORIGINAL_IMAGE_PATH = "product/full"
IMAGE_PATH = "product/image"
IMAGE_WEBP_PATH = "product/image-webp"
THUMBNAIL_PATH = "product/thumbnail"
THUMBNAIL_WEBP_PATH = "product/thumbnail-webp"

IMAGE_SIZE = (1024, 1024)
THUMB_SIZE = (384, 384)
QUALITY = 90

SMS_NUMBER = "+985000125475"

ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/{authority}"

BOOL_CHOICES = (
    (True, "Yes"),
    (False, "No"),
)

USABLE_FOR_CHOICES = (
    (0, "None"),
    (1, "All"),
    (2, "Wholesale"),
    (3, "Retail"),
)

PAYMENT_CHOICES = (
    (0, "آنلاین"),
    (1, "در محل"),
)

PRICE_REGEX = RegexValidator(
    # IN CASE OF EMERGENCY
    # ^(([1-9]\d*)*|[0])$
    # BREAK GLASS
    regex=r"^([1-9]\d*|[0])$",
    message="Price must only contain digits and start with a non-zero number.",
)

ORDER_STATUS = (
    (-3, "Auth Failed"),
    (-2, "Failed"),
    (-1, "Cancelled"),
    (0, "Not paid"),
    (1, "Recieved"),
    (2, "Ongoing"),
    (3, "Completed"),
)
