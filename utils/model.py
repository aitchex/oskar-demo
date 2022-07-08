import hashlib
import pathlib
import time
from io import BytesIO

from django.db import models
from django.core.files import File

from PIL import Image as PillowImage

from utils.const import IMAGE_SIZE, ORIGINAL_IMAGE_PATH, QUALITY, THUMB_SIZE


def generate_thumbnail(image_model: models.Model):
    if image_model.original_image:
        img = PillowImage.open(image_model.original_image)

        if not ORIGINAL_IMAGE_PATH in image_model.original_image.name:
            SIZE = img.width if img.height > img.width else img.height
            ORIGINAL_EXT = img.format.lower()
            JPEG = "jpeg"
            WEBP = "webp"
            RGB = "RGB"

            image = img.crop((0, 0, SIZE, SIZE))
            image.thumbnail(IMAGE_SIZE)
            image = image.convert(RGB)

            image_io = BytesIO()
            image_webp_io = BytesIO()

            image.save(
                image_io,
                format=JPEG,
                quality=QUALITY,
                optimize=True,
            )
            image.save(
                image_webp_io,
                format=WEBP,
                quality=QUALITY,
                optimize=True,
            )

            thumb = img.crop((0, 0, SIZE, SIZE))
            thumb.thumbnail(THUMB_SIZE)
            thumb = thumb.convert(RGB)

            thumb_io = BytesIO()
            thumb_webp_io = BytesIO()

            thumb.save(
                thumb_io,
                format=JPEG,
                quality=QUALITY,
                optimize=True,
            )
            thumb.save(
                thumb_webp_io,
                format=WEBP,
                quality=QUALITY,
                optimize=True,
            )

            while True:
                name = hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()
                path = pathlib.Path(image_model.original_image.path).parent
                orig_name = name + "." + ORIGINAL_EXT

                if not path.joinpath(orig_name).exists():
                    break

            jpeg_name = name + "." + JPEG
            webp_name = name + "." + WEBP

            image_model.original_image.name = orig_name
            image_model.image = File(image_io, jpeg_name)
            image_model.image_webp = File(image_webp_io, webp_name)
            image_model.thumbnail = File(thumb_io, jpeg_name)
            image_model.thumbnail_webp = File(thumb_webp_io, webp_name)

    else:
        image_model.image = None
        image_model.image_webp = None
        image_model.thumbnail = None
        image_model.thumbnail_webp = None
