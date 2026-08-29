from django.urls import path

from . import views

urlpatterns = [
    path("panier/", views.cart, name="cart"),
    path("commande/", views.checkout, name="checkout"),
]