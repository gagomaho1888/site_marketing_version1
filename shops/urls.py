from django.urls import path

from . import views

urlpatterns = [
    path("<slug:slug>/", views.shop_detail, name="shop_detail"),
]