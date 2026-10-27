from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.static import serve

urlpatterns = [
    path(
        "static/dashboard/cnps-logo.png",
        serve,
        {
            "path": "dashboard/cnps-logo.png",
            "document_root": settings.BASE_DIR / "dashboard" / "static",
        },
    ),
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
]

urlpatterns += staticfiles_urlpatterns()
