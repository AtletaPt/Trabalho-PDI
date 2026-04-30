from django.urls import path
from . import views

urlpatterns = [
    path(
        "", views.lista_cabazes, name="lista_cabazes"
    ),  # Agora será acessível em /cabazes/
    path("<int:cabaz_id>/", views.detalhe_cabaz, name="detalhe_cabaz"),
]
