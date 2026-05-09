from django.contrib import admin
from .models import Order, OrderItem

# Esta classe permite que os produtos apareçam dentro da página da encomenda
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Não mostra linhas em branco extra
    readonly_fields = ('product_name',) # Opcional: impede que alteres o nome do produto no admin
    can_delete = False # Impede que apagues itens individuais da encomenda por acidente

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # O que aparece na lista geral de encomendas
    list_display = ('id', 'customer', 'delivery_date', 'status', 'zip_code')
    
    # O que aparece quando clicas numa encomenda específica
    inlines = [OrderItemInline]
    
    # Adiciona filtros laterais para facilitar a gestão
    list_filter = ('status', 'delivery_date', 'zone')
    
    # Permite pesquisar pelo nome do cliente ou ID
    search_fields = ('customer__username', 'id')
