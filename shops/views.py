from django.shortcuts import render, get_object_or_404

from .models import Shop


def shop_detail(request, slug):
    shop = get_object_or_404(Shop, slug=slug)
    return render(request, "shops/detail.html", {"shop": shop})