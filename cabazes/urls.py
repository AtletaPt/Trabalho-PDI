from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),              # página inicial
    path('cabazes/', views.lista_cabazes, name='lista_cabazes'),  # lista de cabazes
]