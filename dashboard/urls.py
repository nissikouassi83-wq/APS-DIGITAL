from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .models import DashboardAccount


class DashboardPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "dashboard/password_change.html"
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        response = super().form_valid(form)
        account, _ = DashboardAccount.objects.get_or_create(user=self.request.user)
        account.must_change_password = False
        account.save(update_fields=["must_change_password"])
        return response

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
        DashboardPasswordChangeView.as_view(),
        name="password_change",
    ),
]
