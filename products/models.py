from django.db import models
from django.conf import settings


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, default="kg")

    producers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProducerProduct",
        limit_choices_to={"user_type": "producer"},
    )

    def __str__(self):
        return self.name


class ProducerProduct(models.Model):
    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "producer"},
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_supplied = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producer.username} - {self.product.name}"
