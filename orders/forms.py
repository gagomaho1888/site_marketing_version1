from django import forms


class CheckoutForm(forms.Form):

    name = forms.CharField(
        label="Nom complet",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex : Aminata Diallo",
                "required": True,
            }
        ),
    )

    phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex : 77 123 45 67",
                "required": True,
            }
        ),
    )

    zone = forms.CharField(
        label="Votre zone / quartier",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex : Ouakam, Dakar",
                "required": True,
            }
        ),
    )