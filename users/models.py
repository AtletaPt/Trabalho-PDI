from django.contrib.auth.models import AbstractUser
from django.db import models

# Tipos de utilizador
USER_TYPES = (
    ('client', 'Cliente'),
    ('producer', 'Produtor'),
    ('admin', 'Administrador'),
)

class CustomUser(AbstractUser):
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='client')

    # Campos adicionais do produtor
    company_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
