from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Order, OrderItem


@admin.action(
    description="Annuler les commandes sélectionnées (restituer le stock)"
)
def cancel_orders(modeladmin, request, queryset):
    count = 0
    for order in queryset:
        if order.cancel():
            count += 1
    modeladmin.message_user(
        request,
        f"{count} commande(s) annulée(s) — stock restitué une seule fois.",
    )


class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "price",
        "subtotal",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    actions = (cancel_orders,)

    list_display = (
        "id",
        "customer_name",
        "customer_phone",
        "shop",
        "total",
        "status",
        "whatsapp_sent",
        "stock_restored_display",
        "created_at",
    )

    list_filter = (
        "status",
        "whatsapp_sent",
        "stock_restored",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "customer_phone",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "stock_restored",
    )

    inlines = [
        OrderItemInline,
    ]

    def stock_restored_display(self, obj):
        if obj.stock_restored:
            return mark_safe('<b style="color:#27ae60;">Oui</b>')
        return "Non"

    stock_restored_display.short_description = "Stock restitué"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "product",
        "quantity",
        "price",
        "subtotal",
    )

    search_fields = (
        "product__name",
    )