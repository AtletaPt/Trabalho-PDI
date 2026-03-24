from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_cabazes, name='lista_cabazes'),
]