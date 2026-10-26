from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Product
from shops.models import Shop


class ShopAccessTests(TestCase):

    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="testpass",
        )
        self.owner_shop = Shop.objects.create(
            owner=self.owner,
            name="Alice Shop",
            slug="alice-shop",
            whatsapp_number="+221 77 123 45 67",
        )
        self.product = Product.objects.create(
            shop=self.owner_shop,
            name="Chemise test",
            slug="chemise-test",
            price=15000,
            stock=5,
        )

    def test_user_without_shop_cannot_manage_first_shop_product(self):
        intruder = get_user_model().objects.create_user(
            username="intruder",
            email="intruder@example.com",
            password="testpass",
        )
        self.client.force_login(intruder)

        response = self.client.get(
            reverse("product_update", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("product_delete", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_other_shop_cannot_manage_product(self):
        other = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass",
        )
        Shop.objects.create(
            owner=other,
            name="Other Shop",
            slug="other-shop",
            whatsapp_number="+221 77 000 00 00",
        )
        self.client.force_login(other)

        response = self.client.get(
            reverse("product_update", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_user_without_shop_redirected_from_dashboard(self):
        user = get_user_model().objects.create_user(
            username="nobody",
            email="nobody@example.com",
            password="testpass",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("boutique"))
        self.assertRedirects(response, reverse("home"))


class ProductSearchTests(TestCase):

    def test_invalid_limit_does_not_raise_server_error(self):
        response = self.client.get(
            reverse("product_search"),
            {"q": "chemise", "limit": "abc"},
        )
        self.assertEqual(response.status_code, 200)
