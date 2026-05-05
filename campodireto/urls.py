from xml.dom.minidom import Document
from django.contrib import admin
from django.urls import path, include
from cabazes import views as cabazes_views
from django.contrib.auth import views as auth_views  # Adiciona esta importação
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    # Homepage real
    path("", cabazes_views.home, name="home"),
    # Autenticação (Resolve o erro do NoReverseMatch)
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="users/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Apps
    path("cabazes/", include("cabazes.urls")),
    path("orders/", include("orders.urls")),
    path("users/", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
