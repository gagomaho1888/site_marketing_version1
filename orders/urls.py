from django.urls import path

from . import views

urlpatterns = [
    path("panier/", views.cart, name="cart"),
    path("panier/ajouter/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("panier/modifier/<int:pk>/", views.update_cart, name="update_cart"),
    path("panier/supprimer/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("commande/", views.checkout, name="checkout"),
    path("confirmation/<int:pk>/", views.order_confirmation, name="confirmation"),
]