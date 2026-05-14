from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

# Isto vai buscar automaticamente o teu CustomUser, seja ele qual for
User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # Define aqui os campos que queres que apareçam no formulário de registo
        # Normalmente o username e o email são o básico
        fields = ("username", "email")
