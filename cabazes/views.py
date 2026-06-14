from django.shortcuts import render, get_object_or_404
from .models import Cabaz


def home(request):
    return render(request, "home.html")


def lista_cabazes(request):
    cabazes = Cabaz.objects.all().prefetch_related("products")
    return render(request, "cabazes/lista.html", {"cabazes": cabazes})


def detalhe_cabaz(request, cabaz_id):
    cabaz = get_object_or_404(Cabaz, id=cabaz_id)
    return render(request, "cabazes/detalhe.html", {"cabaz": cabaz})
