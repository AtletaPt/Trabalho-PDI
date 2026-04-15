from django.shortcuts import render, redirect, get_object_or_404
from cabazes.models import Cabaz
from .models import Order
from django.utils import timezone
from datetime import datetime, timedelta
from users.models import CustomUser


# Página de encomenda (MOSTRAR)
def pagina_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)

    hoje = timezone.now().date()

    return render(request, 'orders/encomenda.html', {
        'cabaz': cabaz,
        'hoje': hoje
    })


# Confirmar encomenda (CRIAR)
def confirmar_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)

    if request.method == 'POST':
        customer = CustomUser.objects.first()

        quantity = int(request.POST.get('quantity', 1))
        delivery_date_str = request.POST.get('delivery_date')

        delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()

        hoje = timezone.now().date()

        # BLOQUEAR datas passadas
        if delivery_date < hoje:
            return redirect('/cabazes/')

        # BLOQUEAR dias inválidos (0=segunda, 2=quarta, 4=sexta)
        if delivery_date.weekday() not in [0, 2, 4]:
            return redirect('/cabazes/')

        Order.objects.create(
            customer=customer,
            cabaz=cabaz,
            quantity=quantity,
            delivery_date=delivery_date,
            status='pendente'
        )

        return redirect('/')

    return redirect('/cabazes/')