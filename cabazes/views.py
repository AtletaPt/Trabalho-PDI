from django.shortcuts import render
from .models import Cabaz

def home(request):
    return render(request, 'home.html')

def lista_cabazes(request):
    cabazes = Cabaz.objects.all()
    return render(request, 'cabazes/lista.html', {'cabazes': cabazes})