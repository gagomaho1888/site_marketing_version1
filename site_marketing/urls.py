"""
URL configuration for site_marketing project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views
from products import views as product_views

urlpatterns = [
    path('', views.gate, name='gate'),
    path('accueil/', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('produits/', include('products.urls')),
    path('boutique/', product_views.boutique_dashboard, name='boutique'),
    path('boutique/categorie/<slug:slug>/', product_views.boutique_category, name='boutique_category'),
    path('boutique/produit/nouveau/', product_views.product_create, name='product_create'),
    path('boutique/produit/<int:pk>/modifier/', product_views.product_update, name='product_update'),
    path('boutique/produit/<int:pk>/supprimer/', product_views.product_delete, name='product_delete'),
    path('boutiques/', include('shops.urls')),
    path('commandes/', include('orders.urls')),
    path('utilisateurs/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
