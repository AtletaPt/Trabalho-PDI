from django.urls import path
from . import views

urlpatterns = [
    path('orders/encomendar/<int:cabaz_id>/', views.pagina_encomenda, name='pagina_encomenda'),
    path('orders/confirmar/<int:cabaz_id>/', views.confirmar_encomenda, name='confirmar_encomenda'),
]