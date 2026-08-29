from django.conf import settings
from django.db import models


class Shop(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop"
    )

    name = models.CharField(max_length=150)

    slug = models.SlugField(
        unique=True,
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    logo = models.ImageField(
        upload_to="shops/logos/",
        blank=True,
        null=True
    )

    cover_image = models.ImageField(
        upload_to="shops/covers/",
        blank=True,
        null=True
    )

    whatsapp_number = models.CharField(
        max_length=30
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True
    )

    address = models.CharField(
        max_length=255,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    instagram_url = models.URLField(
        blank=True
    )

    facebook_url = models.URLField(
        blank=True
    )

    tiktok_url = models.URLField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

# Create your models here.
