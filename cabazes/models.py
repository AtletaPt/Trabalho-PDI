from django.db import models
from products.models import Product

CABAZ_TYPES = (
    ("frutas", "Frutas"),
    ("legumes", "Legumes"),
    ("misto", "Misto"),
    ("personalizado", "Personalizado"),
)


class Cabaz(models.Model):
    name = models.CharField(max_length=50, choices=CABAZ_TYPES)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to="cabazes_images/", blank=True, null=True)
    products = models.ManyToManyField(Product, blank=True)

    # --- NOVA PROPRIEDADE DINÂMICA ---
    @property
    def stock(self):
        """
        Calcula dinamicamente o stock do cabaz com base no produto
        associado que tiver o menor stock na base de dados.
        """
        produtos_do_cabaz = self.products.all()

        # Se o cabaz não tiver produtos associados (ex: um personalizado vazio), o stock é 0
        if not produtos_do_cabaz.exists():
            return 0

        # O stock do cabaz é ditado pelo produto mais escasso
        return min(produto.stock for produto in produtos_do_cabaz)

    def __str__(self):
        return f"{self.get_name_display()} - {self.price}€"
