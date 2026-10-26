from django.db import models, transaction
from shops.models import Shop
from products.models import Product


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("confirmed", "Confirmée"),
        ("preparing", "En préparation"),
        ("delivered", "Livrée"),
        ("cancelled", "Annulée"),
    ]

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    customer_name = models.CharField(
        max_length=150
    )

    customer_phone = models.CharField(
        max_length=30
    )

    customer_address = models.CharField(
        max_length=255,
        blank=True
    )

    customer_city = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    whatsapp_sent = models.BooleanField(
        default=False
    )

    stock_restored = models.BooleanField(
        default=False,
        help_text="Le stock a-t-il été restitué lors d'une annulation ?"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Commande #{self.id}"

    def cancel(self):
        """Annule la commande et restitue le stock (une seule fois)."""
        if self.status == "cancelled":
            return False
        self.status = "cancelled"
        self.save()
        return True

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            cancelling = (
                previous
                and previous.status != "cancelled"
                and self.status == "cancelled"
                and not previous.stock_restored
            )
        else:
            cancelling = False

        if cancelling:
            with transaction.atomic():
                from products.stock import restore_stock

                lines = [
                    {
                        "product_id": item.product_id,
                        "size": item.size,
                        "quantity": item.quantity,
                    }
                    for item in self.items.all()
                ]
                restore_stock(lines)
                self.stock_restored = True

        super().save(*args, **kwargs)


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    size = models.CharField(
        max_length=30,
        blank=True
    )

    color = models.CharField(
        max_length=50,
        blank=True
    )

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity