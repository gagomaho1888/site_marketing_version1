from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from shops.models import Shop

from .forms import ProductForm
from .fuzzy import word_similarity
from .models import CLOTHING_SIZE_CHOICES, SHOE_SIZE_CHOICES, Category, Product


def _size_form_context():
    return {
        "clothing_size_choices": [c[0] for c in CLOTHING_SIZE_CHOICES],
        "shoe_size_choices": [c[0] for c in SHOE_SIZE_CHOICES],
    }


def product_list(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True).order_by("-created_at")
    current_category = None

    category_slug = request.GET.get("categorie")
    if category_slug:
        current_category = categories.filter(slug=category_slug).first()

    if current_category:
        products = products.filter(category=current_category)

    search_query = request.GET.get("q", "").strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    page_obj = Paginator(products, 9).get_page(request.GET.get("page"))
    page_range = page_obj.paginator.get_elided_page_range(page_obj.number)

    return render(request, "products/list.html", {
        "products": page_obj,
        "categories": categories,
        "current_category": current_category,
        "search_query": search_query,
        "page_obj": page_obj,
        "page_range": page_range,
    })


def product_search(request):
    query = request.GET.get("q", "").strip()
    limit = min(int(request.GET.get("limit", 8)), 20)

    if not query:
        return JsonResponse({"query": query, "results": []})

    base = Product.objects.filter(is_active=True).select_related("category")

    category_slug = request.GET.get("categorie")
    if category_slug:
        base = base.filter(category__slug=category_slug)

    ql = query.lower()
    exact = base.filter(Q(name__icontains=query) | Q(description__icontains=query))

    results = list(exact[:limit])
    if len(results) < limit:
        pool = base.exclude(pk__in=[p.pk for p in results])
        fuzzy = []
        for p in pool.iterator():
            sim = word_similarity(query, p.name)
            if sim != float("inf"):
                fuzzy.append((sim, p))
        fuzzy.sort(key=lambda x: x[0])
        for sim, p in fuzzy[: limit - len(results)]:
            results.append(p)

    data = [
        {
            "id": p.pk,
            "name": p.name,
            "price": str(p.price),
            "category": p.category.name if p.category else "",
            "image": p.image.url if p.image and p.image.name else "",
            "url": reverse("product_detail", args=[p.pk]),
            "available": (p.total_available_stock() > 0) if p.size_stocks.exists() else (p.stock > 0),
        }
        for p in results
    ]

    return JsonResponse({"query": query, "results": data})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    available_sizes = []
    if product.size_stocks.exists():
        available_sizes = [
            s for s in product.size_stocks.all() if s.stock > 0
        ]
    return render(request, "products/detail.html", {
        "product": product,
        "available_sizes": available_sizes,
    })


def _get_shop(user):
    shop = getattr(user, "shop", None)
    return shop or Shop.objects.first()


@login_required
def boutique_dashboard(request):
    shop = _get_shop(request.user)
    categories = Category.objects.filter(is_active=True).annotate(
        num_products=Count("products", filter=Q(products__shop=shop))
    )

    return render(request, "products/dashboard.html", {
        "shop": shop,
        "categories": categories,
    })


@login_required
def boutique_category(request, slug):
    shop = _get_shop(request.user)
    category = get_object_or_404(
        Category, slug=slug, is_active=True
    )
    products = Product.objects.filter(shop=shop, category=category) if shop else Product.objects.none()
    categories = Category.objects.filter(is_active=True)

    return render(request, "products/boutique_category.html", {
        "shop": shop,
        "category": category,
        "products": products,
        "categories": categories,
    })


@login_required
def product_create(request):
    shop = _get_shop(request.user)
    if not shop:
        messages.error(request, "Aucune boutique disponible pour cet utilisateur.")
        return redirect("boutique")

    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.instance.shop = shop
        product = form.save()
        messages.success(request, f"L'article « {product.name} » a été ajouté.")
        return redirect("boutique")

    return render(request, "products/product_form.html", {
        "form": form,
        "title": "Ajouter un article",
        **_size_form_context(),
    })


@login_required
def product_update(request, pk):
    shop = _get_shop(request.user)
    product = get_object_or_404(Product, pk=pk, shop=shop)

    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"L'article « {product.name} » a été modifié.")
        return redirect("boutique")

    return render(request, "products/product_form.html", {
        "form": form,
        "product": product,
        "title": f"Modifier — {product.name}",
        **_size_form_context(),
    })


@login_required
def product_delete(request, pk):
    shop = _get_shop(request.user)
    product = get_object_or_404(Product, pk=pk, shop=shop)

    if request.method == "POST":
        product.delete()
        messages.success(request, f"L'article « {product.name} » a été supprimé.")
        return redirect("boutique")

    return render(request, "products/product_confirm_delete.html", {"product": product})