from django import forms
from django.utils.text import slugify

from .models import CLOTHING_SIZE_CHOICES, SHOE_SIZE_CHOICES, ProductSizeStock, Product

CLOTHING_SIZES = [c[0] for c in CLOTHING_SIZE_CHOICES]
SHOE_SIZES = [c[0] for c in SHOE_SIZE_CHOICES]


class ProductForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.initial["is_active"] = True
            self.fields["is_active"].widget = forms.HiddenInput()

        self.fields["image"].required = False

        existing = {}
        if self.instance.pk:
            existing = {s.size: s.stock for s in self.instance.size_stocks.all()}

        self.size_fields = {}

        for size in CLOTHING_SIZES:
            field = forms.IntegerField(
                required=False,
                min_value=0,
                initial=existing.get(size),
                widget=forms.NumberInput(
                    attrs={"class": "form-control form-control-sm", "min": "0", "data-size": size, "data-kind": "clothing"}
                ),
                label=size,
            )
            self.fields[f"size_{size}"] = field
            self.size_fields[size] = field

        for size in SHOE_SIZES:
            field = forms.IntegerField(
                required=False,
                min_value=0,
                initial=existing.get(size),
                widget=forms.NumberInput(
                    attrs={"class": "form-control form-control-sm", "min": "0", "data-size": size, "data-kind": "shoe"}
                ),
                label=size,
            )
            self.fields[f"size_{size}"] = field
            self.size_fields[size] = field

        for name, field in self.fields.items():
            if name.startswith("size_") or name == "category":
                continue
            css = "form-select" if name == "category" else "form-control"
            field.widget.attrs.setdefault("class", css)

    class Meta:
        model = Product
        fields = (
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def _category_name(self):
        category = self.cleaned_data.get("category") or self.instance.category
        return category.name.strip().lower() if category else ""

    def clean(self):
        cleaned = super().clean()
        category_name = self._category_name()

        if category_name == "chaussure":
            active = {s: cleaned.get(f"size_{s}") for s in SHOE_SIZES}
        elif category_name in ("vetement du bas", "vetement du haut"):
            active = {s: cleaned.get(f"size_{s}") for s in CLOTHING_SIZES}
        else:
            active = {}

        self._active_sizes = {s: (v or 0) for s, v in active.items() if v}

        image = cleaned.get("image")
        if not image and self.instance.pk and self.instance.image:
            cleaned["image"] = self.instance.image

        return cleaned

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            base = slugify(product.name)
            slug = base
            counter = 1
            while Product.objects.filter(shop=product.shop, slug=slug).exists():
                counter += 1
                slug = f"{base}-{counter}"
            product.slug = slug
        if commit:
            product.save()

        sizes = getattr(self, "_active_sizes", {})
        if commit:
            ProductSizeStock.objects.filter(product=product).delete()
            for size, stock in sizes.items():
                ProductSizeStock.objects.create(product=product, size=size, stock=stock)

        return product
