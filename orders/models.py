from django.db import models
from users.models import CustomUser
from cabazes.models import Cabaz
from logistics.models import Zone, Vehicle, Driver


ORDER_STATUS = (
    ('pendente', 'Pendente'),
    ('confirmada', 'Confirmada'),
    ('preparacao', 'Em Preparação'),
    ('distribuicao', 'Em Distribuição'),
    ('entregue', 'Entregue'),
    ('cancelada', 'Cancelada'),
)


class Order(models.Model):

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cabaz = models.ForeignKey(Cabaz, on_delete=models.CASCADE)

    quantity = models.IntegerField(default=1)

    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField()

    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True)

    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='pendente'
    )

    def __str__(self):
        return f"Encomenda {self.id} - {self.customer.username}"
