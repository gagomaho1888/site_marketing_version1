from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class GateAccessTests(TestCase):

    def test_non_staff_user_cannot_log_in_through_admin_gate(self):
        get_user_model().objects.create_user(
            username="client",
            email="client@example.com",
            password="testpass",
        )

        response = self.client.post(
            reverse("gate"),
            {"action": "admin", "username": "client", "password": "testpass"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_user_can_log_in_through_admin_gate(self):
        get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass",
            is_staff=True,
        )

        response = self.client.post(
            reverse("gate"),
            {"action": "admin", "username": "admin", "password": "testpass"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)
