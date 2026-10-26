from django.contrib.auth import get_user_model
from django.test import TestCase

from orders.models import Order
from products.models import Product, ProductSizeStock
from shops.models import Shop


class StockManagementBase(TestCase):
    """Base commune : boutique + produit sans tailles (stock global)."""

    def setUp(self):
        user = get_user_model().objects.create_user(
            username="stockuser",
            password="testpass",
        )
        self.shop = Shop.objects.create(
            owner=user,
            name="Alice Shop",
            slug="alice-stock-shop",
            whatsapp_number="+221 77 123 45 67",
        )
        self.product = Product.objects.create(
            shop=self.shop,
            name="T-shirt noir",
            slug="t-shirt-noir",
            price=10000,
            stock=10,
        )

    def put_in_cart(self, product, size="", quantity=1, stock_source=None):
        """Injecte directement la ligne dans le panier de session.

        Simule un panier dont les quantités dépassent le stock réel,
        indépendamment des limites appliquées à l'ajout.
        """
        session = self.client.session
        session["cart"] = {f"{product.pk}:{size}": quantity}
        session.save()

    def checkout(self, **overrides):
        data = {"name": "Aminata", "phone": "771112233", "zone": "Ouakam"}
        data.update(overrides)
        return self.client.post("/commandes/commande/", data)


class StockDecrementTests(StockManagementBase):
    """Tests 1, 2 et 6 : la commande diminue le stock."""

    def test_order_3_of_10_leaves_7(self):
        self.put_in_cart(self.product, quantity=3)
        response = self.checkout()
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_order_2_of_2_leaves_0(self):
        self.product.stock = 2
        self.product.save()
        self.put_in_cart(self.product, quantity=2)
        response = self.checkout()
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)

    def test_order_with_inactive_product_is_rejected(self):
        self.put_in_cart(self.product, quantity=1)
        self.product.is_active = False
        self.product.save()
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Votre panier est vide", response.content.decode())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertFalse(Order.objects.exists())

    def test_order_with_deleted_product_is_rejected(self):
        self.put_in_cart(self.product, quantity=1)
        self.product.delete()
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Votre panier est vide", response.content.decode())
        self.assertFalse(Order.objects.exists())


class StockInsufficientTests(StockManagementBase):
    """Tests 3 et 4 : commande refusée sans toucher au stock."""

    def test_order_3_with_stock_2_is_refused(self):
        self.product.stock = 2
        self.product.save()
        self.put_in_cart(self.product, quantity=3)
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Stock insuffisant", response.content.decode())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)
        self.assertFalse(Order.objects.exists())

    def test_order_1_with_stock_0_is_refused(self):
        self.product.stock = 0
        self.product.save()
        self.put_in_cart(self.product, quantity=1)
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertIn("rupture de stock", response.content.decode())
        self.assertFalse(Order.objects.exists())

    def test_cart_not_cleared_when_refused(self):
        self.product.stock = 1
        self.product.save()
        self.put_in_cart(self.product, quantity=2)
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Stock insuffisant", response.content.decode())
        page = self.client.get("/commandes/panier/")
        self.assertIn("T-shirt noir", page.content.decode())

    def test_add_to_cart_rejects_when_stock_zero(self):
        self.product.stock = 0
        self.product.save()
        response = self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        self.assertEqual(response.status_code, 302)
        page = self.client.get("/commandes/panier/")
        self.assertIn("Votre panier est vide", page.content.decode())

    def test_add_to_cart_caps_quantity_at_stock(self):
        response = self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "50", "next": "cart"},
        )
        self.assertEqual(response.status_code, 302)
        page = self.client.get("/commandes/panier/")
        content = page.content.decode()
        self.assertIn('value="10"', content)


class StockConcurrencyTests(StockManagementBase):
    """Test 5 : deux commandes simultanées de 1 avec un stock de 1."""

    def test_only_one_of_two_orders_succeeds(self):
        self.product.stock = 1
        self.product.save()

        data = {"name": "A", "phone": "1", "zone": "Z"}

        session = self.client.session
        session["cart"] = {f"{self.product.pk}:": 1}
        session.save()
        resp_a = self.client.post("/commandes/commande/", data)
        self.assertEqual(resp_a.status_code, 302)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)

        second = self.client.__class__()
        session = second.session
        session["cart"] = {f"{self.product.pk}:": 1}
        session.save()
        resp_b = second.post("/commandes/commande/", data)
        self.assertEqual(resp_b.status_code, 200)
        self.assertIn("rupture de stock", resp_b.content.decode())

        self.assertEqual(Order.objects.count(), 1)


class MultiProductOrderTests(StockManagementBase):
    """Test 6 : chaque stock est diminué individuellement."""

    def test_each_stock_decremented(self):
        second = Product.objects.create(
            shop=self.shop,
            name="Jean bleu",
            slug="jean-bleu",
            price=20000,
            stock=5,
        )
        with_size = Product.objects.create(
            shop=self.shop,
            name="Chemise M",
            slug="chemise-m",
            price=15000,
            stock=5,
        )
        ProductSizeStock.objects.create(product=with_size, size="M", stock=4)

        session = self.client.session
        session["cart"] = {
            f"{self.product.pk}:": 2,
            f"{second.pk}:": 1,
            f"{with_size.pk}:M": 3,
        }
        session.save()

        response = self.checkout()
        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(second.stock, 4)
        size_row = ProductSizeStock.objects.get(product=with_size, size="M")
        self.assertEqual(size_row.stock, 1)


class OrderPersistenceTests(StockManagementBase):
    """Test 15 : prix conservé, historique conservé après désactivation."""

    def test_order_snapshot_and_items_created(self):
        self.put_in_cart(self.product, quantity=2)
        response = self.checkout()
        self.assertEqual(response.status_code, 302)

        order = Order.objects.get()
        self.assertEqual(order.customer_name, "Aminata")
        self.assertEqual(order.total, 20000)
        item = order.items.get()
        self.assertEqual(item.price, 10000)
        self.assertEqual(item.quantity, 2)

        self.product.price = 12000
        self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.price, 10000)

    def test_deactivated_product_keeps_order_history(self):
        self.put_in_cart(self.product, quantity=1)
        self.checkout()
        self.product.is_active = False
        self.product.save()

        order = Order.objects.get()
        item = order.items.get()
        self.assertEqual(item.product, self.product)
        self.assertEqual(Order.objects.count(), 1)


class StockCancellationTests(StockManagementBase):
    """Test 7 : l'annulation restitue le stock une seule fois."""

    def _place_order(self, quantity=2):
        self.put_in_cart(self.product, quantity=quantity)
        response = self.checkout()
        self.assertEqual(response.status_code, 302)
        return Order.objects.get()

    def test_cancel_restores_stock_once(self):
        order = self._place_order(quantity=2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        order.cancel()
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertTrue(order.stock_restored)
        self.assertEqual(self.product.stock, 10)

        self.assertFalse(order.cancel())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_saving_cancelled_status_twice_does_not_double_restore(self):
        order = self._place_order(quantity=1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)

        order.cancel()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

        order.status = "cancelled"
        order.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_cancel_restores_size_stock(self):
        with_size = Product.objects.create(
            shop=self.shop,
            name="Chemise M",
            slug="chemise-m",
            price=15000,
            stock=5,
        )
        ProductSizeStock.objects.create(product=with_size, size="M", stock=3)

        session = self.client.session
        session["cart"] = {f"{with_size.pk}:M": 2}
        session.save()
        response = self.checkout()
        self.assertEqual(response.status_code, 302)

        size_row = ProductSizeStock.objects.get(product=with_size, size="M")
        self.assertEqual(size_row.stock, 1)

        order = Order.objects.get()
        order.cancel()
        size_row.refresh_from_db()
        self.assertEqual(size_row.stock, 3)


class CartStockLimitTests(StockManagementBase):
    """Limites de quantité appliquées côté serveur dans le panier."""

    def test_update_cart_caps_quantity_at_stock(self):
        session = self.client.session
        session["cart"] = {f"{self.product.pk}:": 2}
        session.save()

        self.client.post(
            f"/commandes/panier/modifier/{self.product.pk}/",
            {"size": "", "quantity": "9"},
        )
        page = self.client.get("/commandes/panier/")
        self.assertIn('value="9"', page.content.decode())  # stock = 10, 9 < 10

        self.client.post(
            f"/commandes/panier/modifier/{self.product.pk}/",
            {"size": "", "quantity": "99"},
        )
        page = self.client.get("/commandes/panier/")
        self.assertIn('value="10"', page.content.decode())  # limité au stock

    def test_update_cart_removes_out_of_stock_item(self):
        session = self.client.session
        session["cart"] = {f"{self.product.pk}:": 2}
        session.save()

        self.product.stock = 0
        self.product.save()

        self.client.post(
            f"/commandes/panier/modifier/{self.product.pk}/",
            {"size": "", "quantity": "2"},
        )
        page = self.client.get("/commandes/panier/")
        self.assertIn("Votre panier est vide", page.content.decode())