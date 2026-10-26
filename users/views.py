from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import SignUpForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription réussie. Vous pouvez vous connecter.")
            return redirect("login")

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session["mode_client"] = False
            messages.success(request, f"Bienvenue, {user.username} !")
            return redirect("home")
        messages.error(request, "Identifiant ou mot de passe incorrect.")

    return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    request.session["mode_client"] = False
    messages.info(request, "Vous êtes déconnecté.")
    return redirect("home")