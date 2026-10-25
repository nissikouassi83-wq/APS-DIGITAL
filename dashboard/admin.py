from django.contrib import admin
from .models import Alerte, Contact, KpiGlobal, Reclamation, Semaine

admin.site.register(Semaine)
admin.site.register(KpiGlobal)
admin.site.register(Reclamation)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("semaine", "motif", "appels", "mails", "messages", "total")
    list_filter = ("semaine",)
    search_fields = ("motif",)


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ("semaine", "section", "type", "texte")
    list_filter = ("semaine", "section", "type")
