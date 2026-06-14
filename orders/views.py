from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import date, datetime
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required

from cabazes.models import Cabaz
from .models import Order, OrderItem
from logistics.models import Zone, Vehicle, Driver

from cabazes.models import Cabaz

from .models import Order, OrderItem
from logistics.models import Zone, Vehicle, Driver

import json
from django.http import JsonResponse


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
                # Verificação de Stock
                for item in cabaz.items.all():
                    necessario = item.quantity * quantity_ordered
                    if item.product.stock < necessario:
                        messages.error(
                            request, f"Stock insuficiente: {item.product.name}."
                        )
                        return redirect("pagina_encomenda", cabaz_id=cabaz.id)

                # Atribuição Logística
                zona_atribuida = get_object_or_404(Zone, id=zona_id)
                veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()
                motorista_atribuido = Driver.objects.first()

                # Criar Encomenda
                nova_encomenda = Order.objects.create(
                    customer=customer,
                    delivery_date=delivery_date,
                    address_detail=morada_detalhada,
                    status="pendente",
                    zone=zona_atribuida,
                    vehicle=veiculo_atribuido,
                    driver=motorista_atribuido,
                    total_price=cabaz.price * quantity_ordered,
                )

                # Criar o Item da Encomenda
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

            return render(request, "orders/sucesso.html", {"order": nova_encomenda})

        except Exception as e:
            # ESTA LINHA É CRUCIAL: Vai dizer-te no terminal por que falhou
            print(f"ERRO AO GERAR SUCESSO: {e}")
            messages.error(request, f"Erro: {str(e)}")
            return redirect("pagina_encomenda", cabaz_id=cabaz.id)

    # Caso GET
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
    if not request.user.is_authenticated:
        messages.warning(
            request, "Precisa de iniciar sessão para adicionar produtos ao carrinho! 🔑"
        )
        return redirect("login")
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

            # 4. Calcular o preço total antecipadamente para o PayPal
            total_da_encomenda = 0
            for cabaz_id, dados in carrinho_sessao.items():
                cabaz = Cabaz.objects.get(id=int(cabaz_id))
                qtd = dados.get("quantidade", 1)
                total_da_encomenda += cabaz.price * qtd

            # 5. GUARDAR NA SESSÃO: Em vez de criar a encomenda na BD agora,
            # guardamos os dados do formulário para usar após o pagamento.
            request.session["dados_encomenda_pendente"] = {
                "zone_id": zona_id,
                "address_detail": morada_detalhada,
                "delivery_date": data_str,
                "total": float(total_da_encomenda),
            }
            request.session.modified = True

            # 6. Redirecionar para a página intermédia com o botão do PayPal
            return render(
                request,
                "orders/pagamentos_paypal.html",
                {"total": total_da_encomenda, "morada": morada_detalhada},
            )

        except Exception as e:
            messages.error(request, f"Erro ao processar os dados do formulário: {e}")
            return redirect("ver_carrinho")

    return redirect("ver_carrinho")


@login_required
@transaction.atomic
def pagamento_sucesso_ajax(request):
    """
    Esta função é chamada via JavaScript (fetch) assim que o PayPal
    aprova o pagamento na Sandbox. Ela cria a encomenda real na BD.
    """
    if request.method == "POST":
        try:
            dados_ajax = json.loads(request.body)

            # Recuperar os dados guardados na sessão
            dados_encomenda = request.session.get("dados_encomenda_pendente")
            carrinho_sessao = request.session.get("carrinho", {})

            if not dados_encomenda or not carrinho_sessao:
                return JsonResponse(
                    {"status": "erro", "message": "Os dados da sessão expiraram."},
                    status=400,
                )

            # Obter a Logística (Igual à tua lógica antiga)
            zona_atribuida = get_object_or_404(Zone, id=dados_encomenda["zone_id"])
            veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()
            motorista_atribuido = Driver.objects.first()
            data_entrega = datetime.strptime(
                dados_encomenda["delivery_date"], "%Y-%m-%d"
            ).date()

            # Criar a Encomenda Oficial
            nova_encomenda = Order.objects.create(
                customer=request.user,
                delivery_date=data_entrega,
                address_detail=dados_encomenda["address_detail"],
                status="pago",  # Define logo como pago!
                zone=zona_atribuida,
                vehicle=veiculo_atribuido,
                driver=motorista_atribuido,
            )

            total_da_encomenda = 0

            # Criar os Itens (OrderItems)
            for cabaz_id, dados in carrinho_sessao.items():
                cabaz = Cabaz.objects.get(id=int(cabaz_id))
                qtd = dados.get("quantidade", 1)
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

            # Atualizar preço final e gravar
            nova_encomenda.total_price = total_da_encomenda
            nova_encomenda.save()

            # Limpar Carrinho e dados pendentes da sessão
            request.session["carrinho"] = {}
            if "dados_encomenda_pendente" in request.session:
                del request.session["dados_encomenda_pendente"]

            # Guardamos o ID para que a view 'ordem_sucesso' saiba que encomenda mostrar
            request.session["ultima_encomenda_id"] = nova_encomenda.id
            request.session.modified = True

            # Retorna o sinal verde para o JavaScript saber para onde redirecionar o browser
            return JsonResponse(
                {"status": "sucesso", "redirect_url": "/orders/sucesso/"}
            )

        except Exception as e:
            return JsonResponse({"status": "erro", "message": str(e)}, status=500)

    return JsonResponse(
        {"status": "erro", "message": "Método não permitido"}, status=405
    )


@login_required
def ordem_sucesso(request):
    """
    Passo 3: Aterragem final do utilizador. Mostra os detalhes da entrega
    e o check verde. Protegido para só mostrar se houver uma compra recente.
    """
    encomenda_id = request.session.get("ultima_encomenda_id")

    if not encomenda_id:
        return redirect("home")

    encomenda = get_object_or_404(Order, id=encomenda_id, customer=request.user)

    return render(request, "orders/sucesso.html", {"order": encomenda})


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
