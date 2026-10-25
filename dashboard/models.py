from django.db import models


class Semaine(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True)
    periode = models.CharField(max_length=60, blank=True)
    fichier = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"Semaine {self.numero}"


class Contact(models.Model):
    """Un motif de contact pour une semaine, ventilé par canal."""
    semaine = models.ForeignKey(Semaine, on_delete=models.CASCADE, related_name="contacts")
    motif = models.CharField(max_length=200)
    appels = models.PositiveIntegerField(default=0)
    mails = models.PositiveIntegerField(default=0)
    messages = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["semaine__numero", "-total"]

    def __str__(self):
        return f"S{self.semaine.numero} - {self.motif}: {self.total}"


class KpiGlobal(models.Model):
    """Volumes globaux (demandes d'informations, assistances e-CNPS, ...)."""
    semaine = models.ForeignKey(Semaine, on_delete=models.CASCADE, related_name="kpis")
    indicateur = models.CharField(max_length=120)
    appels = models.PositiveIntegerField(default=0)
    mails = models.PositiveIntegerField(default=0)
    messages = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"S{self.semaine.numero} - {self.indicateur}: {self.total}"


class Reclamation(models.Model):
    semaine = models.OneToOneField(Semaine, on_delete=models.CASCADE, related_name="reclamation")
    periode = models.CharField(max_length=60, blank=True)
    recues = models.IntegerField(null=True, blank=True)
    recues_semaine_prec = models.IntegerField(null=True, blank=True)
    en_cours = models.IntegerField(null=True, blank=True)
    resolues = models.IntegerField(null=True, blank=True)
    backlog_recues = models.IntegerField(null=True, blank=True)
    backlog_en_cours = models.IntegerField(null=True, blank=True)
    backlog_resolues = models.IntegerField(null=True, blank=True)
    hors_delai_25j = models.IntegerField(null=True, blank=True)
    taux_resolution_pct = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Réclamations S{self.semaine.numero}"


class Alerte(models.Model):
    TYPES = [("alerte", "Point d'alerte"), ("action", "Action à venir")]
    semaine = models.ForeignKey(Semaine, on_delete=models.CASCADE, related_name="alertes")
    section = models.CharField(max_length=60)
    type = models.CharField(max_length=10, choices=TYPES)
    texte = models.TextField()

    def __str__(self):
        return f"S{self.semaine.numero} [{self.type}] {self.texte[:50]}"
