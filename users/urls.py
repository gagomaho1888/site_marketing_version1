from django.urls import path

from . import views

urlpatterns = [
    path("connexion/", views.login_view, name="login"),
    path("inscription/", views.register_view, name="register"),
    path("deconnexion/", views.logout_view, name="logout"),
]