from django.db import models
from shops.models import Shop

CLOTHING_SIZE_CHOICES = [
    ("XXS", "XXS"),
    ("XS", "XS"),
    ("S", "S"),
    ("M", "M"),
    ("L", "L"),
    ("XL", "XL"),
    ("XXL", "XXL (2XL)"),
    ("XXXL", "XXXL (3XL)"),
    ("4XL", "4XL"),
    ("5XL", "5XL"),
]

SHOE_SIZE_CHOICES = [(str(i), str(i)) for i in range(32, 48)]


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Product(models.Model):

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="products"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    name = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        max_length=220
    )

    description = models.TextField(
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    image = models.ImageField(
        upload_to="products/"
    )

    is_active = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

    def total_available_stock(self):
        return sum(s.stock for s in self.size_stocks.all())


class ProductSizeStock(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="size_stocks",
    )

    size = models.CharField(
        max_length=30,
    )

    stock = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["size"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "size"],
                name="unique_product_size",
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.stock})"
