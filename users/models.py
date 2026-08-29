from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Utilisateur du site.
    Pour la V1, il représente principalement le propriétaire de la boutique.
    """

    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username