from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
from cabazes.models import Cabaz
from .models import Order
from users.models import CustomUser
from logistics.models import Zone, Vehicle, Driver 


# Página de encomenda (MOSTRAR FORMULÁRIO)
def pagina_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)
    hoje = timezone.now().date()

    return render(request, 'orders/encomenda.html', {
        'cabaz': cabaz,
        'hoje': hoje
    })


# Confirmar encomenda (CRIAR REGISTO COM LOGÍSTICA AUTOMÁTICA)
def confirmar_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)

    if request.method == 'POST':
        # usar o primeiro utilizador disponível
        customer = CustomUser.objects.first()
        
        quantity = int(request.POST.get('quantity', 1))
        delivery_date_str = request.POST.get('delivery_date')

        # Validação da data
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Data de entrega inválida.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')

        hoje = timezone.now().date()

        # BLOQUEAR datas passadas
        if delivery_date < hoje:
            messages.error(request, "Não pode escolher uma data que já passou.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')

        # BLOQUEAR dias que não sejam Segunda(0), Quarta(2) ou Sexta(4)
        if delivery_date.weekday() not in [0, 2, 4]:
            messages.error(request, "Entregas disponíveis apenas à Segunda, Quarta e Sexta.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')
        
        # Tentar obter a primeira zona registada no sistema
        zona_atribuida = Zone.objects.first()
        
        # obter o veículo que pertence a essa zona
        veiculo_atribuido = None
        if zona_atribuida:
            veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()
        
        # obter o primeiro motorista registado
        motorista_atribuido = Driver.objects.first()

        # --- Criação da Encomenda ---
        Order.objects.create(
            customer=customer,
            cabaz=cabaz,
            quantity=quantity,
            delivery_date=delivery_date,
            status='pendente',
            zone=zona_atribuida,          
            vehicle=veiculo_atribuido,    
            driver=motorista_atribuido     
        )

        messages.success(request, f"Encomenda de {cabaz.get_name_display()} realizada com sucesso!")
        return redirect('/')

    return redirect('/cabazes/')