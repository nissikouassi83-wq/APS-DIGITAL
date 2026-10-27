from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "connexion/",
        auth_views.LoginView.as_view(template_name="dashboard/login.html"),
        name="login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "mot-de-passe/",
        auth_views.PasswordChangeView.as_view(
            template_name="dashboard/password_change.html",
            success_url=reverse_lazy("index"),
        ),
        name="password_change",
    ),
]
