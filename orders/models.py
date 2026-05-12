from django.db import models
from users.models import CustomUser
from cabazes.models import Cabaz
from logistics.models import Zone, Vehicle, Driver

ORDER_STATUS = (
    ("pendente", "Pendente"),
    ("confirmada", "Confirmada"),
    ("preparacao", "Em Preparação"),
    ("distribuicao", "Em Distribuição"),
    ("entregue", "Entregue"),
    ("cancelada", "Cancelada"),
)


class Order(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    # Removemos o campo 'cabaz' daqui, porque ele agora vai para o OrderItem

    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField()
    address_detail = models.CharField(
        max_length=255, verbose_name="Morada (Rua, Nº, Andar) "
    )
    zip_code = models.CharField(max_length=10, blank=True, null=True)

    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True)
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True
    )

    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pendente")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Encomenda {self.id} - {self.customer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    cabaz = models.ForeignKey(Cabaz, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # CAMPO CHAVE: Aqui guardamos os produtos escolhidos (ex: "Maçã, Pêra, Laranja")
    selected_products = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.cabaz.name} na Encomenda {self.order.id}"
