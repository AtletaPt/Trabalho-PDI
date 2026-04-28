from django.shortcuts import render
from .models import Cabaz

def home(request):
    return render(request, 'home.html')

def lista_cabazes(request):
    # O nome correto aqui é 'products', que é o que está no teu models.py
    cabazes = Cabaz.objects.all().prefetch_related('products')
    return render(request, 'cabazes/lista.html', {'cabazes': cabazes})