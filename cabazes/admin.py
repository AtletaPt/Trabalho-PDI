# cabazes/admin.py
from django.contrib import admin
from .models import Cabaz


@admin.register(Cabaz)
class CabazAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "weight")
