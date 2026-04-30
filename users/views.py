from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages


def registo_view(request):
    # Verifica se o utilizador foi redirecionado porque tentou aceder a algo restrito
    if "next" in request.GET and not request.user.is_authenticated:
        # Usamos messages.error para que apareça a vermelho conforme o teu base.html
        messages.error(
            request,
            "Para finalizar a encomenda, deve ter uma conta. Por favor, crie uma conta ou faça login.",
        )

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(
                request, f"Conta criada para {username}! Já pode fazer login."
            )
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "users/registo.html", {"form": form})
