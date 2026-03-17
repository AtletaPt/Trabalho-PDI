from django.db import models
from products.models import Product

# Tipos de cabaz
CABAZ_TYPES = (
    ('frutas', 'Frutas'),
    ('legumes', 'Legumes'),
    ('misto', 'Misto'),
    ('personalizado', 'Personalizado'),
)

class Cabaz(models.Model):
    name = models.CharField(max_length=50, choices=CABAZ_TYPES)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='cabazes_images/', blank=True, null=True)
    products = models.ManyToManyField(Product, blank=True)  # lista genérica de produtos

    def __str__(self):
        return f"{self.get_name_display()} - {self.price}€"
