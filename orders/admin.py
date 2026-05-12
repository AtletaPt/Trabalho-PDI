from django.contrib import admin
from .models import Order, OrderItem


# 1. Configuração para os produtos aparecerem dentro da página da Encomenda
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Impede que apareçam linhas vazias extras
    readonly_fields = (
        "cabaz",
        "quantity",
        "price",
        "selected_products",
    )


# 2. Configuração principal da Encomenda
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Campos que aparecem na LISTA principal (tabela inicial)
    list_display = ("id", "customer", "delivery_date", "zone", "status")

    # Organização dos campos dentro do formulário de edição
    fieldsets = (
        ("Informação do Cliente", {"fields": ("customer", "status", "total_price")}),
        (
            "Logística e Entrega",
            {
                "fields": (
                    "delivery_date",
                    "address_detail",
                    "zone",
                    "vehicle",
                    "driver",
                )
            },
        ),
    )

    # Inserir os produtos (OrderItem) dentro da página da Encomenda
    inlines = [OrderItemInline]

    readonly_fields = ("total_price",)


# 3. Registo opcional para ver os itens isoladamente
admin.site.register(OrderItem)
