from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import date, datetime
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required

from cabazes.models import Cabaz
from .models import Order, OrderItem
from logistics.models import Zone, Vehicle, Driver

# orders/views.py

from cabazes.models import Cabaz

# ADICIONA 'OrderItem' aqui à frente de 'Order'
from .models import Order, OrderItem
from logistics.models import Zone, Vehicle, Driver


def pagina_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)
    hoje = timezone.now().date()
    return render(request, "orders/encomenda.html", {"cabaz": cabaz, "hoje": hoje})


@login_required
def confirmar_encomenda(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)

    if request.method == "POST":
        customer = request.user
        quantity_ordered = int(request.POST.get("quantity", 1))
        delivery_date_str = request.POST.get("delivery_date")

        # NOVOS CAMPOS vindos do formulário
        zona_id = request.POST.get("zone_id")
        morada_detalhada = request.POST.get("address_detail")

        # 1. VALIDAÇÃO DE DATA
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Data inválida.")
            return redirect("pagina_encomenda", cabaz_id=cabaz.id)

        hoje = timezone.now().date()
        if delivery_date < hoje:
            messages.error(request, "Não pode encomendar para datas passadas.")
            return redirect("pagina_encomenda", cabaz_id=cabaz.id)

        if delivery_date.weekday() not in [0, 2, 4]:
            messages.error(request, "Entregas apenas à Segunda, Quarta e Sexta.")
            return redirect("pagina_encomenda", cabaz_id=cabaz.id)

        # 2. LOGÍSTICA E STOCK COM TRANSAÇÃO
        try:
            with transaction.atomic():
                # Verificação de Stock (Mantemos a tua lógica)
                for item in cabaz.items.all():
                    necessario = item.quantity * quantity_ordered
                    if item.product.stock < necessario:
                        messages.error(
                            request, f"Stock insuficiente: {item.product.name}."
                        )
                        return redirect("pagina_encomenda", cabaz_id=cabaz.id)

                # Atribuição Logística Baseada no ID da Zona (Nova Lógica)
                zona_atribuida = get_object_or_404(Zone, id=zona_id)
                veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()
                motorista_atribuido = Driver.objects.first()

                # Criar Encomenda (Utilizando address_detail e total_price)
                nova_encomenda = Order.objects.create(
                    customer=customer,
                    delivery_date=delivery_date,
                    address_detail=morada_detalhada,  # Agora gravamos a morada exata
                    status="pendente",
                    zone=zona_atribuida,
                    vehicle=veiculo_atribuido,
                    driver=motorista_atribuido,
                    total_price=cabaz.price * quantity_ordered,
                )

                # Criar o Item da Encomenda (OrderItem)
                # Como é compra direta, os produtos selecionados são os originais do cabaz
                OrderItem.objects.create(
                    order=nova_encomenda,
                    cabaz=cabaz,
                    quantity=quantity_ordered,
                    price=cabaz.price,
                    selected_products=", ".join(
                        [item.product.name for item in cabaz.items.all()]
                    ),
                )

                # Baixa de Stock
                for item in cabaz.items.all():
                    necessario = item.quantity * quantity_ordered
                    item.product.stock -= necessario
                    item.product.save()

            messages.success(request, "Encomenda confirmada com sucesso!")
            return render(request, "orders/sucesso.html", {"order": nova_encomenda})

        except Exception as e:
            messages.error(request, f"Erro ao processar encomenda: {str(e)}")
            return redirect("pagina_encomenda", cabaz_id=cabaz.id)

    # Se o método for GET (quando a página carrega pela primeira vez)
    # Precisas de enviar as zonas para o template poder mostrar o menu select
    zonas = Zone.objects.all()
    return render(
        request,
        "orders/confirmar_encomenda.html",
        {
            "cabaz": cabaz,
            "zonas": zonas,
            "hoje": timezone.now().date().strftime("%Y-%m-%d"),
        },
    )


@login_required
def historico_encomendas(request):
    encomendas = Order.objects.filter(customer=request.user).order_by("-delivery_date")
    return render(request, "orders/historico.html", {"encomendas": encomendas})


def adicionar_ao_carrinho(request, cabaz_id):
    if "carrinho" not in request.session:
        request.session["carrinho"] = {}

    carrinho = request.session["carrinho"]
    id_str = str(cabaz_id)

    # Se o pedido for POST (vindo da página de detalhe)
    if request.method == "POST":
        # Vamos buscar a lista de nomes dos produtos selecionados
        produtos_escolhidos = request.POST.getlist("produtos_escolhidos")

        if not produtos_escolhidos:
            messages.error(request, "Tens de selecionar pelo menos um produto!")
            return redirect("detalhe_cabaz", cabaz_id=cabaz_id)

        # Guardamos no carrinho um dicionário em vez de apenas a quantidade
        # Assim guardamos a quantidade E a lista de produtos para este item
        if id_str in carrinho:
            carrinho[id_str]["quantidade"] += 1
            # Opcional: atualizar os produtos escolhidos ou manter os anteriores
            carrinho[id_str]["produtos"] = produtos_escolhidos
        else:
            carrinho[id_str] = {"quantidade": 1, "produtos": produtos_escolhidos}

        messages.success(request, "Cabaz adicionado ao carrinho!")
    else:
        # Se for um GET simples (ex: botão + no carrinho), apenas aumenta a quantidade
        if id_str in carrinho:
            carrinho[id_str]["quantidade"] += 1
        else:
            # Caso alguém tente adicionar sem passar pelo detalhe,
            # podes redirecionar para o detalhe para ele escolher
            return redirect("detalhe_cabaz", cabaz_id=cabaz_id)

    request.session.modified = True
    return redirect("ver_carrinho")


def ver_carrinho(request):
    carrinho_sessao = request.session.get("carrinho", {})
    itens_display = []
    total_geral = 0

    for cabaz_id, dados in carrinho_sessao.items():
        if not isinstance(dados, dict):
            continue

        cabaz = get_object_or_404(Cabaz, id=int(cabaz_id))
        qtd = dados.get("quantidade", 0)
        produtos = dados.get("produtos", [])

        subtotal = cabaz.price * qtd
        total_geral += subtotal

        itens_display.append(
            {
                "cabaz": cabaz,
                "quantidade": qtd,
                "subtotal": subtotal,
                "produtos_selecionados": produtos,  # Passa a lista de produtos
            }
        )

    # NOVIDADE: Buscar as zonas para o menu de seleção
    zonas = Zone.objects.all()

    return render(
        request,
        "orders/carrinho.html",
        {
            "itens": itens_display,
            "total": total_geral,
            "zonas": zonas,  # ADICIONADO AQUI
            "hoje": date.today().strftime("%Y-%m-%d"),
        },
    )


@login_required
@transaction.atomic
def finalizar_carrinho(request):
    if request.method == "POST":
        # 1. Capturar dados do formulário
        zona_id = request.POST.get("zone_id")
        morada_detalhada = request.POST.get("address_detail")
        data_str = request.POST.get("delivery_date")

        # 2. Validar se o carrinho existe
        carrinho_sessao = request.session.get("carrinho", {})
        if not carrinho_sessao:
            messages.error(request, "O teu carrinho está vazio.")
            return redirect("ver_carrinho")

        try:
            # 3. Validar a Data (Seg, Qua, Sex)
            data_entrega = datetime.strptime(data_str, "%Y-%m-%d").date()
            if data_entrega.weekday() not in [0, 2, 4]:
                messages.error(
                    request,
                    "Data inválida. Entregamos apenas às Segundas, Quartas e Sextas.",
                )
                return redirect("ver_carrinho")

            # 4. Obter a Zona e Logística (Dinamismo Total)
            # Se o utilizador escolheu uma zona, vamos buscar o objeto Zone
            zona_atribuida = get_object_or_404(Zone, id=zona_id)

            # Procurar o veículo associado a esta zona
            veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()

            motorista_atribuido = Driver.objects.first()

            # 5. Criar a Encomenda
            with transaction.atomic():  # Garante que nada é criado se houver erro a meio
                nova_encomenda = Order.objects.create(
                    customer=request.user,
                    delivery_date=data_entrega,
                    address_detail=morada_detalhada,  # Novo campo no modelo
                    status="pendente",
                    zone=zona_atribuida,
                    vehicle=veiculo_atribuido,
                    driver=motorista_atribuido,
                )

                total_da_encomenda = 0

                # 6. Criar os Itens (OrderItems)
                for cabaz_id, dados in carrinho_sessao.items():
                    cabaz = Cabaz.objects.get(id=int(cabaz_id))
                    qtd = dados.get("quantidade", 1)

                    # CORREÇÃO: Tratar a lista de produtos selecionados
                    produtos_lista = dados.get("produtos", [])
                    produtos_str = ", ".join(produtos_lista)

                    OrderItem.objects.create(
                        order=nova_encomenda,
                        cabaz=cabaz,
                        quantity=qtd,
                        price=cabaz.price,
                        selected_products=produtos_str,
                    )
                    total_da_encomenda += cabaz.price * qtd

                # Atualizar preço final
                nova_encomenda.total_price = total_da_encomenda
                nova_encomenda.save()

                # 7. Limpar Carrinho
                request.session["carrinho"] = {}
                request.session.modified = True

                messages.success(request, "Encomenda realizada com sucesso!")
                return redirect("historico_encomendas")

        except Exception as e:
            messages.error(request, f"Erro ao processar a encomenda: {e}")
            return redirect("ver_carrinho")

    return redirect("ver_carrinho")


def remover_do_carrinho(request, cabaz_id):
    carrinho = request.session.get("carrinho", {})
    id_str = str(cabaz_id)

    # Verifica se o utilizador quer apagar tudo de uma vez
    delete_all = request.GET.get("action") == "delete"
    if id_str in carrinho:
        if delete_all or carrinho[id_str]["quantidade"] <= 1:
            del carrinho[id_str]
        else:
            carrinho[id_str]["quantidade"] -= 1
        request.session.modified = True

    return redirect("ver_carrinho")
