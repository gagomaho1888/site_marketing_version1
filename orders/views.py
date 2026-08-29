from django.shortcuts import render


def cart(request):
    return render(request, "orders/cart.html")


def checkout(request):
    return render(request, "orders/checkout.html")