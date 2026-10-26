"""Gestion atomique du stock des produits (avec et sans tailles).

La concurrence est gérée par des UPDATE conditionnels (WHERE stock >= quantité),
atomiques au niveau SQL, ce qui est fiable avec SQLite même sans SELECT FOR UPDATE.
"""

from django.db import transaction
from django.db.models import F

from .models import Product, ProductSizeStock


class StockError(Exception):
    """Erreur de disponibilité de stock, affichée au client."""


def available_quantity(product, size=""):
    """Quantité actuellement disponible pour un produit (avec ou sans taille)."""
    if size:
        row = ProductSizeStock.objects.filter(
            product_id=product.pk, size=size
        ).values_list("stock", flat=True).first()
        return row or 0
    return product.stock


def _insufficient_message(product_name, size, available):
    if available <= 0:
        return f"« {product_name} » est en rupture de stock."
    suffix = f" (taille {size})" if size else ""
    return (
        f"Stock insuffisant pour « {product_name} »{suffix} : "
        f"seulement {available} disponible(s)."
    )


@transaction.atomic
def reserve_stock(lines):
    """Vérifie et diminue le stock de chaque ligne de commande.

    lines = [{"product_id": int, "size": str, "quantity": int}]
    Lève StockError si un produit manque, est inactif ou si le stock est insuffisant.
    """
    for line in lines:
        product = Product.objects.filter(
            pk=line["product_id"], is_active=True
        ).first()
        if product is None:
            raise StockError("Un des articles n'est plus disponible.")
        quantity = line["quantity"]
        if quantity <= 0:
            raise StockError("Quantité invalide.")
        _apply_decrement(product, line["size"], quantity)


def _apply_decrement(product, size, quantity):
    if size:
        stock = ProductSizeStock.objects.filter(
            product_id=product.pk, size=size
        )
        updated = stock.filter(stock__gte=quantity).update(
            stock=F("stock") - quantity
        )
        if not updated:
            current = stock.values_list("stock", flat=True).first() or 0
            raise StockError(_insufficient_message(product.name, size, current))
    else:
        updated = Product.objects.filter(
            pk=product.pk, stock__gte=quantity
        ).update(stock=F("stock") - quantity)
        if not updated:
            current = (
                Product.objects.filter(pk=product.pk)
                .values_list("stock", flat=True)
                .first()
                or 0
            )
            raise StockError(_insufficient_message(product.name, "", current))


@transaction.atomic
def restore_stock(lines):
    """Rend les quantités au stock (annulation de commande).

    Ne peut pas échouer : si une taille a disparu, le stock global est utilisé.
    """
    for line in lines:
        product = Product.objects.filter(pk=line["product_id"]).first()
        if product is None:
            continue
        quantity = line["quantity"]
        if quantity <= 0:
            continue
        if line["size"]:
            restored = ProductSizeStock.objects.filter(
                product_id=product.pk, size=line["size"]
            ).update(stock=F("stock") + quantity)
            if not restored:
                Product.objects.filter(pk=product.pk).update(
                    stock=F("stock") + quantity
                )
        else:
            Product.objects.filter(pk=product.pk).update(
                stock=F("stock") + quantity
            )