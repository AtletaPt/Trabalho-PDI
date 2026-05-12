from django.contrib import admin
from .models import Order, OrderItem


# Configuração para os produtos aparecerem dentro da página da Encomenda
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Impede que apareçam linhas vazias extras
    readonly_fields = (
        "cabaz",
        "quantity",
        "price",
        "selected_products",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # O que aparece na lista principal de encomendas
    list_display = ("id", "customer", "delivery_date", "status", "total_price", "zone")

    # Filtros laterais para facilitar a gestão
    list_filter = ("status", "delivery_date", "zone")

    # Campo de pesquisa (por nome de utilizador ou ID)
    search_fields = ("customer__username", "id")

    # Organiza os campos dentro da encomenda
    fieldsets = (
        ("Informação do Cliente", {"fields": ("customer", "status")}),
        (
            "Logística e Entrega",
            {"fields": ("delivery_date", "zip_code", "zone", "vehicle", "driver")},
        ),
        (
            "Financeiro",
            {
                "fields": ("total_price",),
            },
        ),
    )

    # Inserir os produtos selecionados dentro da Encomenda
    inlines = [OrderItemInline]


# Se quiseres ver os itens isoladamente (opcional)
admin.site.register(OrderItem)
