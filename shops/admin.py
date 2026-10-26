from django.contrib import admin
from .models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "owner",
        "whatsapp_number",
        "city",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "city",
    )

    search_fields = (
        "name",
        "owner__username",
        "whatsapp_number",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }
# Register your models here.
