from django.shortcuts import render, redirect
from cabazes.models import Cabaz
from .models import Order
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser
from django.contrib import messages

def criar_encomenda(request, cabaz_id):
    cabaz = Cabaz.objects.get(id=cabaz_id)

    customer = CustomUser.objects.first()

    # data de entrega (ex: amanhã)
    delivery_date = timezone.now().date() + timedelta(days=1)

    order = Order.objects.create(
        customer=customer,
        cabaz=cabaz,
        quantity=1,
        delivery_date=delivery_date,
        status='pendente'
    )

    return redirect('/')