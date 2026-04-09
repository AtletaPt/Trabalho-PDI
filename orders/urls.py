from django.urls import path
from . import views

urlpatterns = [
    path('orders/encomendar/<int:cabaz_id>/', views.criar_encomenda, name='criar_encomenda'),
]