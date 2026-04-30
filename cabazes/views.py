from django.shortcuts import render, get_object_or_404
from .models import Cabaz


def home(request):
    return render(request, "home.html")


def lista_cabazes(request):
    # O nome correto aqui é 'products', que é o que está no teu models.py
    cabazes = Cabaz.objects.all().prefetch_related("products")
    return render(request, "cabazes/lista.html", {"cabazes": cabazes})


def detalhe_cabaz(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)
    # Filtramos apenas os cabazes que não são o personalizado para já
    return render(request, "cabazes/detalhe.html", {"cabaz": cabaz})
