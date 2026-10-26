from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render

from products.models import Product, Category

ADMIN_USERNAME = "Alice"


def gate(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "admin":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "")
            if username != ADMIN_USERNAME:
                messages.error(request, "Accès réservé à l'administrateur.")
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    request.session["mode_client"] = False
                    messages.success(request, f"Bienvenue, {user.username} !")
                    return redirect("home")
                messages.error(request, "Identifiant ou mot de passe incorrect.")
        elif action == "client":
            request.session["mode_client"] = True
            return redirect("home")

    return render(request, "home/gate.html")


def home(request):
    featured = Product.objects.filter(is_featured=True, is_active=True)[:8]
    if not featured.exists():
        featured = Product.objects.filter(is_active=True)[:8]
    context = {
        "featured_products": featured,
        "categories": Category.objects.filter(is_active=True),
    }
    return render(request, "home/accueil.html", context)