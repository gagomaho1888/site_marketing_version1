from django.contrib.auth import get_user_model
from django.test import TestCase

from products.models import Product, ProductSizeStock
from shops.models import Shop


class CartFlowTests(TestCase):

    def setUp(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass",
        )
        self.shop = Shop.objects.create(
            owner=user,
            name="Alice Shop",
            slug="alice-shop",
            whatsapp_number="+221 77 123 45 67",
        )
        self.product = Product.objects.create(
            shop=self.shop,
            name="Chemise test",
            slug="chemise-test",
            price=15000,
            stock=5,
        )

    def test_add_and_list_cart(self):
        response = self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "2", "next": "cart"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/commandes/panier/")

        page = self.client.get("/commandes/panier/")
        self.assertEqual(page.status_code, 200)
        content = page.content.decode()
        self.assertIn("Chemise test", content)
        self.assertIn("30000.00 FCFA", content)

    def test_add_with_size_appears_in_cart(self):
        ProductSizeStock.objects.create(product=self.product, size="M", stock=3)
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"size": "M", "quantity": "1", "next": "cart"},
        )
        page = self.client.get("/commandes/panier/")
        content = page.content.decode()
        self.assertIn("Taille : M", content)

    def test_add_without_size_is_rejected(self):
        ProductSizeStock.objects.create(product=self.product, size="M", stock=3)
        response = self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        self.assertRedirects(
            response, f"/produits/{self.product.pk}/"
        )
        self.assertEqual(self.client.get("/commandes/panier/").content.decode().count("Chemise test"), 0)

    def test_add_same_item_cumulates(self):
        for _ in range(2):
            self.client.post(
                f"/commandes/panier/ajouter/{self.product.pk}/",
                {"quantity": "1", "next": "cart"},
            )
        page = self.client.get("/commandes/panier/")
        content = page.content.decode()
        self.assertIn('value="2"', content)

    def test_update_quantity(self):
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        self.client.post(
            f"/commandes/panier/modifier/{self.product.pk}/",
            {"size": "", "quantity": "4"},
        )
        content = self.client.get("/commandes/panier/").content.decode()
        self.assertIn('value="4"', content)

    def test_remove_item(self):
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        self.client.post(
            f"/commandes/panier/supprimer/{self.product.pk}/",
            {"size": ""},
        )
        page = self.client.get("/commandes/panier/")
        self.assertIn("Votre panier est vide", page.content.decode())

    def test_empty_cart_page(self):
        page = self.client.get("/commandes/panier/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Votre panier est vide", page.content.decode())


class CheckoutTests(TestCase):

    def setUp(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass",
        )
        self.shop = Shop.objects.create(
            owner=user,
            name="Alice Shop",
            slug="alice-shop",
            whatsapp_number="+221 77 123 45 67",
        )
        self.product = Product.objects.create(
            shop=self.shop,
            name="Chemise test",
            slug="chemise-test",
            price=15000,
            stock=5,
        )

    def test_checkout_page_shows_cart_items_and_form(self):
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        response = self.client.get("/commandes/commande/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Chemise test", content)
        self.assertIn("Nom complet", content)
        self.assertIn("Numéro de téléphone", content)
        self.assertIn("Votre zone", content)

    def test_checkout_without_cart_shows_empty_message(self):
        response = self.client.get("/commandes/commande/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Votre panier est vide", response.content.decode())

    def test_checkout_shows_confirmation_and_whatsapp_link(self):
        from orders.models import Order

        ProductSizeStock.objects.create(product=self.product, size="M", stock=3)
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"size": "M", "quantity": "2", "next": "cart"},
        )

        response = self.client.post(
            "/commandes/commande/",
            {"name": "Aminata", "phone": "771112233", "zone": "Ouakam"},
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertIn(f"/commandes/confirmation/{order.pk}/", response["Location"])

        page = self.client.get(f"/commandes/confirmation/{order.pk}/")
        self.assertEqual(page.status_code, 200)
        content = page.content.decode()
        self.assertIn("Votre commande a bien été enregistrée", content)
        self.assertIn(f"Commande n° {order.pk}", content)
        self.assertIn("https://wa.me/221771234567", content)
        self.assertIn("Alice+Shop", content)
        self.assertIn("Chemise+test", content)
        self.assertIn("Taille+M", content)
        self.assertIn("%C3%97", content)  # "×" encodé
        self.assertIn("Total+%3A+30000.00+FCFA", content)
        self.assertIn("Aminata", content)

    def test_confirmation_is_limited_to_the_customer_session(self):
        from orders.models import Order

        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        self.client.post(
            "/commandes/commande/",
            {"name": "Aminata", "phone": "771112233", "zone": "Ouakam"},
        )
        order = Order.objects.get()

        other_client = self.client_class()
        response = other_client.get(f"/commandes/confirmation/{order.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_refresh_after_checkout_does_not_create_duplicate(self):
        from orders.models import Order

        ProductSizeStock.objects.create(product=self.product, size="M", stock=3)
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"size": "M", "quantity": "2", "next": "cart"},
        )
        self.client.post(
            "/commandes/commande/",
            {"name": "Aminata", "phone": "771112233", "zone": "Ouakam"},
        )
        first = Order.objects.get()

        page = self.client.get("/commandes/commande/")
        self.assertIn("Votre panier est vide", page.content.decode())
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().pk, first.pk)

    def test_checkout_clears_cart(self):
        self.client.post(
            f"/commandes/panier/ajouter/{self.product.pk}/",
            {"quantity": "1", "next": "cart"},
        )
        self.client.post(
            "/commandes/commande/",
            {"name": "Aminata", "phone": "771112233", "zone": "Ouakam"},
        )
        page = self.client.get("/commandes/panier/")
        self.assertIn("Votre panier est vide", page.content.decode())