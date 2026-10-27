from django.shortcuts import redirect
from django.urls import reverse

from .models import DashboardAccount


class RequireInitialPasswordChangeMiddleware:
    allowed_paths = {"/mot-de-passe/", "/deconnexion/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.path.startswith("/admin/")
            and not request.path.startswith("/static/")
            and request.path not in self.allowed_paths
        ):
            account, _ = DashboardAccount.objects.get_or_create(user=request.user)
            if account.must_change_password:
                return redirect(reverse("password_change"))

        return self.get_response(request)
