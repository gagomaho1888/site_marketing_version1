from decimal import Decimal

from products.models import Product
from products.stock import available_quantity


class Cart:
    """Panier stocké en session.

    Structure : { "{product_id}:{size}" : quantité }
    """

    def __init__(self, request):
        self._session = request.session
        self._items = request.session.get("cart", {})

    @staticmethod
    def _key(product_id, size):
        return f"{product_id}:{size or ''}"

    def items(self):
        return dict(self._items)

    def count(self):
        return sum(int(q) for q in self._items.values())

    def add(self, product_id, size, quantity=1):
        key = self._key(product_id, size)
        self._items[key] = self._items.get(key, 0) + quantity
        self._save()

    def update(self, product_id, size, quantity):
        key = self._key(product_id, size)
        if quantity > 0:
            self._items[key] = quantity
        else:
            self._items.pop(key, None)
        self._save()

    def remove(self, product_id, size):
        self._items.pop(self._key(product_id, size), None)
        self._save()

    def clear(self):
        self._items = {}
        self._save()

    def _save(self):
        self._session["cart"] = self._items
        self._session.modified = True


def build_cart_items(raw_cart):
    """Transforme le panier brut en lignes prêtes pour le template.

    Retourne (listes, total) avec :
    - product : le modèle Product
    - size : str
    - quantity : int
    - available : int (stock restant disponible)
    - subtotal : Decimal
    """
    items = []
    total = Decimal("0.00")

    if not raw_cart:
        return items, total

    product_ids = [int(key.split(":", 1)[0]) for key in raw_cart]
    products = {
        p.pk: p
        for p in Product.objects.filter(pk__in=product_ids, is_active=True)
    }

    for key, quantity in raw_cart.items():
        product_id_str, _, size = key.partition(":")
        product = products.get(int(product_id_str))
        if product is None:
            continue
        subtotal = product.price * int(quantity)
        items.append(
            {
                "product": product,
                "size": size,
                "quantity": int(quantity),
                "available": available_quantity(product, size),
                "subtotal": subtotal,
            }
        )
        total += subtotal

    return items, total