from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import Alerte, Contact, KpiGlobal, Reclamation, Semaine
from dashboard.services.extraction import extraire_rapport


class Command(BaseCommand):
    help = "Importe (ou met à jour) les rapports hebdo .pptx du dossier data/pptx"

    def add_arguments(self, parser):
        parser.add_argument("--dossier", default=str(settings.PPTX_DIR))

    def handle(self, *args, **opts):
        fichiers = sorted(Path(opts["dossier"]).glob("*.pptx"))
        if not fichiers:
            self.stdout.write(self.style.WARNING(f"Aucun .pptx dans {opts['dossier']}"))
            return

        for f in fichiers:
            d = extraire_rapport(f)
            with transaction.atomic():
                sem, _ = Semaine.objects.update_or_create(
                    numero=d["numero"],
                    defaults={"periode": d["periode"], "fichier": d["fichier"]},
                )
                # On repart de zéro pour cette semaine : relancer l'import ne crée pas de doublons.
                sem.contacts.all().delete()
                sem.kpis.all().delete()
                sem.alertes.all().delete()
                Reclamation.objects.filter(semaine=sem).delete()

                Contact.objects.bulk_create([Contact(semaine=sem, **m) for m in d["motifs"]])
                KpiGlobal.objects.bulk_create([KpiGlobal(semaine=sem, **k) for k in d["kpis"]])
                Reclamation.objects.create(semaine=sem, **d["reclamation"])
                Alerte.objects.bulk_create([Alerte(semaine=sem, **a) for a in d["alertes"]])

            self.stdout.write(self.style.SUCCESS(
                f"Semaine {d['numero']} importée ({len(d['motifs'])} motifs) <- {f.name}"))
