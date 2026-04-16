from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
from django.db import transaction

from cabazes.models import Cabaz
from .models import Order
from users.models import CustomUser
from logistics.models import Zone, Vehicle, Driver 

def obter_zona_por_cp(zip_code):
    try:
        prefixo, sufixo = zip_code.split('-')
        sufixo = int(sufixo)
    except:
        return None

    # 1. Santo António dos Olivais e Celas
    if prefixo == '3000':
        if sufixo == 5 or (25 <= sufixo <= 46) or sufixo == 48 or sufixo == 101 or sufixo == 119 or \
           (291 <= sufixo <= 293) or sufixo == 299 or sufixo == 304 or sufixo == 313 or sufixo == 353 or \
           (375 <= sufixo <= 377) or (458 <= sufixo <= 459) or sufixo == 538 or sufixo == 540 or (542 <= sufixo <= 543):
            return "Santo António dos Olivais e Celas"
    elif prefixo == '3020':
        if sufixo == 134 or (163 <= sufixo <= 165) or (238 <= sufixo <= 239) or sufixo == 246 or \
           (249 <= sufixo <= 250) or sufixo == 255 or (368 <= sufixo <= 369) or sufixo == 371 or sufixo == 385 or \
           (476 <= sufixo <= 489):
            return "Santo António dos Olivais e Celas"
    elif prefixo == '3030':
        if sufixo in [461, 464, 468, 471, 473] or (477 <= sufixo <= 491) or sufixo == 493 or (775 <= sufixo <= 776):
            return "Santo António dos Olivais e Celas"

    # 2. Coimbra Centro (Baixa e Sé)
    if prefixo == '3000':
        if (20 <= sufixo <= 34) or (97 <= sufixo <= 104) or (114 <= sufixo <= 116) or (120 <= sufixo <= 122) or \
           (282 <= sufixo <= 290) or (294 <= sufixo <= 312) or (315 <= sufixo <= 317) or sufixo == 351 or \
           (355 <= sufixo <= 363) or (365 <= sufixo <= 366) or sufixo in [368, 370] or (372 <= sufixo <= 374) or \
           sufixo == 470 or (472 <= sufixo <= 473) or (475 <= sufixo <= 476) or sufixo in [481, 484] or \
           (486 <= sufixo <= 487) or (489 <= sufixo <= 492) or sufixo == 494 or sufixo == 503 or \
           (507 <= sufixo <= 509) or sufixo == 511 or (515 <= sufixo <= 516) or sufixo == 520 or (522 <= sufixo <= 525):
            return "Coimbra Centro (Baixa e Sé)"

    # 3. Solum e Vale das Flores
    if prefixo == '3030':
        if sufixo == 450 or (452 <= sufixo <= 459):
            return "Solum e Vale das Flores"

    # 4. Eiras e São Paulo de Frades
    if prefixo == '3000' and (106 <= sufixo <= 113):
        return "Eiras e São Paulo de Frades"
    elif prefixo == '3020':
        if (130 <= sufixo <= 133) or (135 <= sufixo <= 136) or sufixo == 154 or sufixo == 164 or \
           (166 <= sufixo <= 171) or sufixo in [239, 240, 248, 251, 308, 384, 438, 458, 478, 497] or \
           (242 <= sufixo <= 244) or (253 <= sufixo <= 254) or (322 <= sufixo <= 324) or \
           (422 <= sufixo <= 424) or (428 <= sufixo <= 430) or (461 <= sufixo <= 462) or (499 <= sufixo <= 500):
            return "Eiras e São Paulo de Frades"

    # 5. São Martinho e Santa Clara
    if prefixo == '3045':
        if (1 <= sufixo <= 199) or (300 <= sufixo <= 999):
            return "São Martinho e Santa Clara"

    return None

def pagina_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)
    hoje = timezone.now().date()
    return render(request, 'orders/encomenda.html', {'cabaz': cabaz, 'hoje': hoje})

def confirmar_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)

    if request.method == 'POST':
        customer = CustomUser.objects.first()
        quantity_ordered = int(request.POST.get('quantity', 1)) 
        delivery_date_str = request.POST.get('delivery_date')
        zip_code = request.POST.get('zip_code', '') 

        # 1. VALIDAÇÕES DE DATA E CP
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Data inválida.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')

        hoje = timezone.now().date()
        if delivery_date < hoje:
            messages.error(request, "Não pode encomendar para datas passadas.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')

        if delivery_date.weekday() not in [0, 2, 4]:
            messages.error(request, "Entregas apenas à Segunda, Quarta e Sexta.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')

        nome_zona = obter_zona_por_cp(zip_code)
        if not nome_zona:
            messages.error(request, f"O Código Postal {zip_code} não é coberto pelas nossas entregas.")
            return redirect(f'/orders/encomendar/{cabaz.id}/')

        # 2. VERIFICAÇÃO PREVENTIVA DE STOCK
        # Usamos atomic() para garantir que nada é gravado se houver erro a meio
        with transaction.atomic():
            # Percorremos os itens do cabaz (ex: 2kg de Batata)
            for item in cabaz.items.all(): 
                necessario = item.quantity * quantity_ordered
                if item.product.stock < necessario:
                    messages.error(request, f"Stock insuficiente: {item.product.name} (Só temos {item.product.stock}).")
                    return redirect(f'/orders/encomendar/{cabaz.id}/')

            # 3. LOGÍSTICA
            zona_atribuida = Zone.objects.filter(name__iexact=nome_zona).first()
            veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()
            motorista_atribuido = Driver.objects.first()

            # 4. CRIAR ENCOMENDA
            nova_encomenda = Order.objects.create(
                customer=customer,
                cabaz=cabaz,
                quantity=quantity_ordered,
                delivery_date=delivery_date,
                status='pendente',
                zone=zona_atribuida,
                vehicle=veiculo_atribuido,
                driver=motorista_atribuido
            )

            # 5. EXECUTAR BAIXA DE STOCK REAL
            for item in cabaz.items.all():
                necessario = item.quantity * quantity_ordered
                item.product.stock -= necessario
                item.product.save()

        messages.success(request, "Encomenda confirmada e inventário atualizado!")
        return render(request, 'orders/sucesso.html', {'order': nova_encomenda})

    return redirect('/cabazes/')