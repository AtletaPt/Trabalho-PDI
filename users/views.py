from django.shortcuts import render, redirect
from django.contrib import messages

# Importa o teu novo formulário personalizado
from .forms import CustomUserCreationForm


def registo_view(request):
    # Verifica se o utilizador foi redirecionado
    if "next" in request.GET and not request.user.is_authenticated:
        messages.error(
            request,
            "Para finalizar a encomenda, deve ter uma conta. Por favor, crie uma conta ou faça login.",
        )

    if request.method == "POST":
        # USAR O FORMULÁRIO PERSONALIZADO AQUI
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(
                request, f"Conta criada para {username}! Já pode fazer login."
            )
            return redirect("login")
    else:
        # E AQUI TAMBÉM
        form = CustomUserCreationForm()

    return render(request, "users/registo.html", {"form": form})
