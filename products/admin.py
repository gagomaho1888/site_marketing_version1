from django.contrib import admin
from django.db.models import F, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils.html import format_html

from .models import Category, Product, ProductSizeStock


class ProductSizeStockInline(admin.TabularInline):
    model = ProductSizeStock
    extra = 1


class StockStatusFilter(admin.SimpleListFilter):
    title = "Disponibilité"
    parameter_name = "dispo"

    def lookups(self, request, model_admin):
        return (
            ("available", "Disponibles"),
            ("low", "Stock faible (≤ 5)"),
            ("out", "Rupture de stock"),
        )

    def _annotate(self, queryset):
        total_sizes = Subquery(
            ProductSizeStock.objects.filter(product=OuterRef("pk"))
            .values("product")
            .annotate(total=Sum("stock"))
            .values("total"),
            output_field=IntegerField(),
        )
        return queryset.annotate(
            _total_available=Coalesce(
                total_sizes, F("stock"), output_field=IntegerField()
            )
        )

    def queryset(self, request, queryset):
        if self.value() == "available":
            return self._annotate(queryset).filter(_total_available__gte=1)
        if self.value() == "low":
            return self._annotate(queryset).filter(_total_available__range=(1, 5))
        if self.value() == "out":
            return self._annotate(queryset).filter(_total_available=0)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    inlines = (ProductSizeStockInline,)

    list_display = (
        "name",
        "shop",
        "category",
        "price",
        "stock",
        "availability_display",
        "is_active",
        "is_featured",
        "created_at",
    )

    list_filter = (
        StockStatusFilter,
        "category",
        "is_active",
        "is_featured",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    list_editable = (
        "price",
        "stock",
        "is_active",
        "is_featured",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("size_stocks")

    @admin.display(description="Disponibilité")
    def availability_display(self, obj):
        rows = obj.size_stocks.all()
        total = sum(s.stock for s in rows) if rows else obj.stock
        if total <= 0:
            return format_html('<b style="color:#c0392b;">Rupture</b>')
        if total <= 5:
            return format_html('<b style="color:#e67e22;">{} dispo</b>', total)
        return format_html('<b style="color:#27ae60;">Disponible</b> ({})', total)

    class Media:
        js = ("products/js/admin_products.js",)
# Register your models here.