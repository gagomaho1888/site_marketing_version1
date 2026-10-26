from django.urls import path

from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("recherche/", views.product_search, name="product_search"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
]