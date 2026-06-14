from django.urls import path
from . import views

urlpatterns = [
    path("encomendar/<int:cabaz_id>/", views.pagina_encomenda, name="pagina_encomenda"),
    path(
        "confirmar/<int:cabaz_id>/",
        views.confirmar_encomenda,
        name="confirmar_encomenda",
    ),
    path("historico/", views.historico_encomendas, name="historico_encomendas"),
    path("carrinho/", views.ver_carrinho, name="ver_carrinho"),
    path(
        "carrinho/adicionar/<int:cabaz_id>/",
        views.adicionar_ao_carrinho,
        name="adicionar_ao_carrinho",
    ),
    path("carrinho/finalizar/", views.finalizar_carrinho, name="finalizar_carrinho"),
    path(
        "carrinho/remover/<int:cabaz_id>/",
        views.remover_do_carrinho,
        name="remover_do_carrinho",
    ),
    path("finalizar/", views.finalizar_carrinho, name="finalizar_carrinho"),
    path(
        "pagamento-sucesso-ajax/",
        views.pagamento_sucesso_ajax,
        name="pagamento_sucesso_ajax",
    ),
    path("sucesso/", views.ordem_sucesso, name="ordem_sucesso"),
]
