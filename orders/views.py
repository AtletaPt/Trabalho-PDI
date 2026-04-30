from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import date, datetime
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required

from cabazes.models import Cabaz
from .models import Order
from logistics.models import Zone, Vehicle, Driver


def obter_zona_por_cp(zip_code):
    try:
        prefixo, sufixo = zip_code.split("-")
        sufixo = int(sufixo)
    except:
        return None

    # 1. Santo António dos Olivais e Celas
    if prefixo == "3000":
        if (
            sufixo == 5
            or (25 <= sufixo <= 46)
            or sufixo == 48
            or sufixo == 101
            or sufixo == 119
            or (291 <= sufixo <= 293)
            or sufixo == 299
            or sufixo == 304
            or sufixo == 313
            or sufixo == 353
            or (375 <= sufixo <= 377)
            or (458 <= sufixo <= 459)
            or sufixo == 538
            or sufixo == 540
            or (542 <= sufixo <= 543)
        ):
            return "Santo António dos Olivais e Celas"
    elif prefixo == "3020":
        if (
            sufixo == 134
            or (163 <= sufixo <= 165)
            or (238 <= sufixo <= 239)
            or sufixo == 246
            or (249 <= sufixo <= 250)
            or sufixo == 255
            or (368 <= sufixo <= 369)
            or sufixo == 371
            or sufixo == 385
            or (476 <= sufixo <= 489)
        ):
            return "Santo António dos Olivais e Celas"
    elif prefixo == "3030":
        if (
            sufixo in [461, 464, 468, 471, 473]
            or (477 <= sufixo <= 491)
            or sufixo == 493
            or (775 <= sufixo <= 776)
        ):
            return "Santo António dos Olivais e Celas"

    # 2. Coimbra Centro (Baixa e Sé)
    if prefixo == "3000":
        if (
            (20 <= sufixo <= 34)
            or (97 <= sufixo <= 104)
            or (114 <= sufixo <= 116)
            or (120 <= sufixo <= 122)
            or (282 <= sufixo <= 290)
            or (294 <= sufixo <= 312)
            or (315 <= sufixo <= 317)
            or sufixo == 351
            or (355 <= sufixo <= 363)
            or (365 <= sufixo <= 366)
            or sufixo in [368, 370]
            or (372 <= sufixo <= 374)
            or sufixo == 470
            or (472 <= sufixo <= 473)
            or (475 <= sufixo <= 476)
            or sufixo in [481, 484]
            or (486 <= sufixo <= 487)
            or (489 <= sufixo <= 492)
            or sufixo == 494
            or sufixo == 503
            or (507 <= sufixo <= 509)
            or sufixo == 511
            or (515 <= sufixo <= 516)
            or sufixo == 520
            or (522 <= sufixo <= 525)
        ):
            return "Coimbra Centro (Baixa e Sé)"

    # 3. Solum e Vale das Flores
    if prefixo == "3030":
        if sufixo == 450 or (452 <= sufixo <= 459):
            return "Solum e Vale das Flores"

    # 4. Eiras e São Paulo de Frades
    if prefixo == "3000" and (106 <= sufixo <= 113):
        return "Eiras e São Paulo de Frades"
    elif prefixo == "3020":
        if (
            (130 <= sufixo <= 133)
            or (135 <= sufixo <= 136)
            or sufixo == 154
            or sufixo == 164
            or (166 <= sufixo <= 171)
            or sufixo in [239, 240, 248, 251, 308, 384, 438, 458, 478, 497]
            or (242 <= sufixo <= 244)
            or (253 <= sufixo <= 254)
            or (322 <= sufixo <= 324)
            or (422 <= sufixo <= 424)
            or (428 <= sufixo <= 430)
            or (461 <= sufixo <= 462)
            or (499 <= sufixo <= 500)
        ):
            return "Eiras e São Paulo de Frades"

    # 5. São Martinho e Santa Clara
    if prefixo == "3045":
        if (1 <= sufixo <= 199) or (300 <= sufixo <= 999):
            return "São Martinho e Santa Clara"

    return None


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
        zip_code = request.POST.get("zip_code", "")

        # 1. VALIDAÇÕES DE DATA E CP
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

        nome_zona = obter_zona_por_cp(zip_code)
        if not nome_zona:
            messages.error(
                request,
                f"O Código Postal {zip_code} não é coberto pelas nossas entregas em Coimbra.",
            )
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
                zona_atribuida = Zone.objects.filter(name__iexact=nome_zona).first()
                veiculo_atribuido = Vehicle.objects.filter(zone=zona_atribuida).first()
                motorista_atribuido = Driver.objects.first()

                # Criar Encomenda
                nova_encomenda = Order.objects.create(
                    customer=customer,
                    cabaz=cabaz,
                    quantity=quantity_ordered,
                    delivery_date=delivery_date,
                    status="pendente",
                    zone=zona_atribuida,
                    vehicle=veiculo_atribuido,
                    driver=motorista_atribuido,
                    zip_code=zip_code,
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

    return redirect("pagina_encomenda", cabaz_id=cabaz_id)


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

        messages.success(request, "Cabaz personalizado adicionado ao carrinho!")
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
        # Proteção contra dados antigos: se não for um dicionário, ignora este item
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
                "produtos_selecionados": produtos,
            }
        )

    return render(
        request,
        "orders/carrinho.html",
        {
            "itens": itens_display,
            "total": total_geral,
            # Usamos date.today() formatado para que o 'min' do HTML funcione 100%
            "hoje": date.today().strftime("%Y-%m-%d"),
        },
    )


@login_required
@transaction.atomic
def finalizar_carrinho(request):
    carrinho = request.session.get("carrinho", {})

    if request.method == "POST":
        if not carrinho:
            return redirect("/cabazes/")

        delivery_date_str = request.POST.get("delivery_date")

        # 1. Tentar converter a data e validar regras de negócio
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()

            # BLOQUEIO 1: Data no passado
            if delivery_date < date.today():
                messages.error(
                    request, "A data de entrega não pode ser anterior a hoje."
                )
                return redirect("/orders/carrinho/")

            # BLOQUEIO 2: Apenas Segunda (0), Quarta (2) e Sexta (4)
            if delivery_date.weekday() not in [0, 2, 4]:
                messages.error(
                    request,
                    "Entregamos apenas às Segundas, Quartas e Sextas em Coimbra.",
                )
                return redirect("/orders/carrinho/")

        except ValueError:
            messages.error(request, "Data de entrega inválida.")
            return redirect("/orders/carrinho/")

        # 2. Validar Zona de Entrega
        nome_zona = obter_zona_por_cp(request.POST.get("zip_code"))
        if not nome_zona:
            messages.error(request, "Infelizmente ainda não chegamos a essa morada.")
            return redirect("/orders/carrinho/")

        zona = Zone.objects.filter(name__iexact=nome_zona).first()
        veiculo = Vehicle.objects.filter(zone=zona).first()
        motorista = Driver.objects.first()

        # 3. Processar itens e criar encomendas
        try:
            for cabaz_id, dados in carrinho.items():
                if not isinstance(dados, dict):
                    continue

                qtd_encomendada = dados.get("quantidade", 0)
                cabaz_obj = Cabaz.objects.get(id=int(cabaz_id))

                # Atualizar Stock de cada produto no cabaz
                for produto in cabaz_obj.products.all():
                    produto.stock -= qtd_encomendada
                    produto.save()

                # Criar a Encomenda na Base de Dados
                Order.objects.create(
                    customer=request.user,
                    cabaz=cabaz_obj,
                    quantity=qtd_encomendada,
                    delivery_date=delivery_date,
                    zone=zona,
                    vehicle=veiculo,
                    driver=motorista,
                    status="pendente",
                )

            # Limpar o carrinho da sessão
            request.session["carrinho"] = {}
            request.session.modified = True

            messages.success(request, "Encomenda finalizada com sucesso!")
            return redirect("/orders/historico/")

        except Exception as e:
            messages.error(request, f"Erro técnico: {str(e)}")
            return redirect("/orders/carrinho/")

    return redirect("/orders/carrinho/")


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
