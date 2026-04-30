from django.urls import path
from . import views

urlpatterns = [
    path("registo/", views.registo_view, name="registo"),
]
