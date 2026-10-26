from urllib.parse import urlencode

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from products.stock import StockError, available_quantity, reserve_stock

from .cart import Cart, build_cart_items
from .forms import CheckoutForm
from .models import Order, OrderItem


def cart(request):
    items, total = build_cart_items(request.session.get("cart", {}))
    return render(request, "orders/cart.html", {"items": items, "total": total})


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    size = request.POST.get("size", "").strip()
    if product.size_stocks.exists() and not size:
        messages.error(request, "Veuillez sélectionner une taille.")
        return redirect("product_detail", pk=pk)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, quantity)

    available = available_quantity(product, size)
    if available <= 0:
        messages.error(request, f"« {product.name} » est en rupture de stock.")
        return redirect("product_detail", pk=pk)

    if quantity > available:
        quantity = available
        messages.warning(
            request,
            f"Quantité limitée à {available} (stock disponible).",
        )

    Cart(request).add(product.pk, size, quantity)
    messages.success(request, "Article ajouté au panier.")

    if request.POST.get("next") == "checkout":
        return redirect("checkout")
    return redirect("cart")


def update_cart(request, pk):
    product = Product.objects.filter(pk=pk, is_active=True).first()
    size = request.POST.get("size", "").strip()

    try:
        quantity = int(request.POST.get("quantity", 0))
    except (TypeError, ValueError):
        quantity = 0

    cart_obj = Cart(request)

    if product is None:
        cart_obj.remove(pk, size)
        messages.error(request, "Cet article n'est plus disponible ; il a été retiré du panier.")
        return redirect("cart")

    if quantity <= 0:
        cart_obj.remove(pk, size)
        return redirect("cart")

    available = available_quantity(product, size)
    if available <= 0:
        cart_obj.remove(pk, size)
        messages.error(
            request,
            f"« {product.name} » est en rupture de stock ; il a été retiré du panier.",
        )
    elif quantity > available:
        cart_obj.update(pk, size, available)
        messages.warning(
            request,
            f"Quantité de « {product.name} » réduite à {available} (stock disponible).",
        )
    else:
        cart_obj.update(pk, size, quantity)

    return redirect("cart")


def remove_from_cart(request, pk):
    size = request.POST.get("size", "").strip()
    Cart(request).remove(pk, size)
    return redirect("cart")


def create_order(items, total, customer_data):
    """Crée la commande et diminue le stock, en une seule transaction.

    items : lignes du panier issues de build_cart_items().
    customer_data : champs nettoyés du CheckoutForm.
    """
    lines = [
        {
            "product_id": item["product"].pk,
            "size": item["size"],
            "quantity": item["quantity"],
        }
        for item in items
    ]

    with transaction.atomic():
        reserve_stock(lines)

        shop = items[0]["product"].shop
        order = Order.objects.create(
            shop=shop,
            customer_name=customer_data["name"],
            customer_phone=customer_data["phone"],
            customer_address=customer_data["zone"],
            total=total,
            status="pending",
            whatsapp_sent=True,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price=item["product"].price,
                size=item["size"],
            )

        return order


def _whatsapp_message(shop, items, total, customer_data):
    lines = []
    for item in items:
        details = ""
        if item["size"]:
            details = f" Taille {item['size']}"
        if item["quantity"] > 1:
            details = f"{details} × {item['quantity']}"
        lines.append(
            f"- {item['product'].name}{details} — {item['subtotal']} FCFA"
        )
    return (
        f"Bonjour {shop.name} \U0001F44B\n"
        f"Je souhaite passer cette commande :\n"
        f"{chr(10).join(lines)}\n"
        f"\nTotal : {total} FCFA\n"
        f"\nNom : {customer_data['name']}\n"
        f"Téléphone : {customer_data['phone']}\n"
        f"Zone : {customer_data['zone']}\n"
    )


def _remember_order(request, order):
    """Garde l'accès à la confirmation limité à la session du client."""
    order_ids = request.session.get("order_ids", [])
    if order.pk not in order_ids:
        order_ids.append(order.pk)
    request.session["order_ids"] = order_ids[-10:]


def checkout(request):
    cart_obj = Cart(request)
    items, total = build_cart_items(cart_obj.items())

    form = CheckoutForm()

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid() and items:
            data = form.cleaned_data
            try:
                order = create_order(items, total, data)
            except StockError as exc:
                messages.error(request, str(exc))
            else:
                _remember_order(request, order)
                cart_obj.clear()
                return redirect("confirmation", pk=order.pk)

    return render(
        request,
        "orders/checkout.html",
        {"items": items, "total": total, "form": form},
    )


def order_confirmation(request, pk):
    """Affiche la confirmation au client et le lien WhatsApp de la commande."""
    if pk not in request.session.get("order_ids", []):
        raise Http404("Commande introuvable.")

    order = get_object_or_404(Order, pk=pk)

    items = []
    for item in order.items.select_related("product"):
        items.append(
            {
                "product": item.product,
                "size": item.size,
                "quantity": item.quantity,
                "price": item.price,
                "subtotal": item.subtotal,
            }
        )

    customer_data = {
        "name": order.customer_name,
        "phone": order.customer_phone,
        "zone": order.customer_address,
    }
    message = _whatsapp_message(order.shop, items, order.total, customer_data)
    number = "".join(ch for ch in order.shop.whatsapp_number if ch.isdigit())
    whatsapp_url = "https://wa.me/" + number + "?" + urlencode({"text": message})

    return render(request, "orders/confirmation.html", {
        "order": order,
        "items": items,
        "whatsapp_url": whatsapp_url,
    })