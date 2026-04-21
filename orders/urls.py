from django.urls import path
from . import views

urlpatterns = [
    path('encomendar/<int:cabaz_id>/', views.pagina_encomenda, name='pagina_encomenda'),
    path('confirmar/<int:cabaz_id>/', views.confirmar_encomenda, name='confirmar_encomenda'),
    path('historico/', views.historico_encomendas, name='historico_encomendas'),
]