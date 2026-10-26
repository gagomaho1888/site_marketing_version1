from products.models import Category
from shops.models import Shop


def boutique_context(request):
    shop = Shop.objects.filter(is_active=True).first()
    return {
        "site_shop": shop,
        "all_categories": Category.objects.filter(is_active=True),
        "whatsapp_url": (
            "https://wa.me/"
            + "".join(ch for ch in shop.whatsapp_number if ch.isdigit())
            if shop and shop.whatsapp_number
            else ""
        ),
    }


def cart_context(request):
    return {
        "cart_count": sum(
            int(q) for q in request.session.get("cart", {}).values()
        )
    }


def admin_context(request):
    return {
        "is_pending_admin": not request.user.is_authenticated
        and not request.session.get("mode_client", False),
    }