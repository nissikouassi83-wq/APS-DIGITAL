from collections import defaultdict

from django.db.models import Sum
from django.shortcuts import render

from .models import Alerte, Contact, KpiGlobal, Reclamation, Semaine

# Indicateurs affichés dans le graphique d'évolution (ordre d'affichage)
INDICATEURS = [
    "DEMANDES D'INFORMATIONS",
    "ASSISTANCES e-CNPS",
    "RECLAMATIONS",
    "SUIVIS DE DOSSIERS",
]


def _carte(label, valeur, precedent, semaine_precedente=None,
           hausse_est_mauvaise=False, suffixe=""):
    """Carte KPI avec variation par rapport à la semaine précédente disponible."""
    if valeur is None:
        return dict(label=label, valeur="–", suffixe="", comparaison="Donnée non disponible",
                    classe="neutre")
    if semaine_precedente is None:
        return dict(label=label, valeur=valeur, suffixe=suffixe,
                    comparaison="Pas de semaine précédente à comparer", classe="neutre")
    if precedent is None:
        return dict(label=label, valeur=valeur, suffixe=suffixe,
                    comparaison=f"Valeur non disponible en S{semaine_precedente}",
                    classe="neutre")
    delta = valeur - precedent
    if delta == 0:
        classe = "neutre"
        comparaison = f"Même valeur qu'en S{semaine_precedente}"
    elif delta > 0:
        classe = "bon" if not hausse_est_mauvaise else "mauvais"
        if suffixe == " %":
            points = "point" if delta == 1 else "points"
            comparaison = f"+{delta} {points} de pourcentage par rapport à S{semaine_precedente}"
        else:
            comparaison = f"{delta} de plus qu'en S{semaine_precedente}"
    else:
        classe = "mauvais" if not hausse_est_mauvaise else "bon"
        if suffixe == " %":
            points = "point" if delta == -1 else "points"
            comparaison = f"{abs(delta)} {points} de pourcentage de moins qu'en S{semaine_precedente}"
        else:
            comparaison = f"{abs(delta)} de moins qu'en S{semaine_precedente}"
    return dict(label=label, valeur=valeur, suffixe=suffixe,
                comparaison=comparaison, classe=classe)


def index(request):
    semaines = list(Semaine.objects.order_by("numero"))
    if not semaines:
        return render(request, "dashboard/index.html", {"vide": True})

    # --- semaine sélectionnée (dernière par défaut)
    choix = request.GET.get("semaine")
    sel = next((s for s in semaines if str(s.numero) == choix), semaines[-1])
    pos = semaines.index(sel)
    prec = semaines[pos - 1] if pos > 0 else None

    labels = [f"S{s.numero}" for s in semaines]
    nums = [s.numero for s in semaines]

    # --- KPI globaux : {(numero, indicateur): objet}
    kpis = {(k.semaine.numero, k.indicateur): k
            for k in KpiGlobal.objects.select_related("semaine")}

    def kpi(num, nom, champ="total"):
        k = kpis.get((num, nom))
        return getattr(k, champ) if k else None

    canaux = dict(
        appels=[kpi(n, "TOTAL", "appels") for n in nums],
        mails=[kpi(n, "TOTAL", "mails") for n in nums],
        messages=[kpi(n, "TOTAL", "messages") for n in nums],
    )
    indicateurs = {nom: [kpi(n, nom) for n in nums] for nom in INDICATEURS}

    # --- Top 10 motifs de la semaine sélectionnée
    top = list(Contact.objects.filter(semaine=sel).order_by("-total")[:10])
    top_motifs = dict(
        motifs=[c.motif for c in top],
        appels=[c.appels for c in top],
        mails=[c.mails for c in top],
        messages=[c.messages for c in top],
    )

    # --- Évolution des 5 motifs les plus fréquents sur toute la période
    top5 = [r["motif"] for r in (Contact.objects.values("motif")
                                 .annotate(t=Sum("total")).order_by("-t")[:5])]
    valeurs = defaultdict(dict)
    for c in Contact.objects.filter(motif__in=top5).select_related("semaine"):
        valeurs[c.motif][c.semaine.numero] = c.total
    evolution = {m: [valeurs[m].get(n, 0) for n in nums] for m in top5}

    # --- Réclamations
    recl = {r.semaine.numero: r for r in Reclamation.objects.select_related("semaine")}

    def rv(num, champ):
        r = recl.get(num)
        return getattr(r, champ) if r else None

    reclamations = dict(
        recues=[rv(n, "recues") for n in nums],
        resolues=[rv(n, "resolues") for n in nums],
        taux=[rv(n, "taux_resolution_pct") for n in nums],
        backlog_en_cours=[rv(n, "backlog_en_cours") for n in nums],
    )

    # --- Cartes KPI
    pn = prec.numero if prec else None
    cartes = [
        _carte("Contacts reçus", kpi(sel.numero, "TOTAL"),
               kpi(pn, "TOTAL") if pn else None, pn),
        _carte("Réclamations reçues", rv(sel.numero, "recues"),
               rv(pn, "recues") if pn else None, pn, hausse_est_mauvaise=True),
        _carte("Taux de résolution", rv(sel.numero, "taux_resolution_pct"),
               rv(pn, "taux_resolution_pct") if pn else None, pn, suffixe=" %"),
        _carte("Backlog en cours", rv(sel.numero, "backlog_en_cours"),
               rv(pn, "backlog_en_cours") if pn else None, pn, hausse_est_mauvaise=True),
        _carte("Assistances e-CNPS", kpi(sel.numero, "ASSISTANCES e-CNPS"),
               kpi(pn, "ASSISTANCES e-CNPS") if pn else None, pn,
               hausse_est_mauvaise=True),
    ]

    alertes = Alerte.objects.filter(semaine=sel)
    data = dict(labels=labels, canaux=canaux, indicateurs=indicateurs,
                top_motifs=top_motifs, evolution=evolution, reclamations=reclamations,
                semaine=f"S{sel.numero}")

    return render(request, "dashboard/index.html", {
        "vide": False,
        "semaines": semaines,
        "sel": sel,
        "prec": prec,
        "cartes": cartes,
        "alertes_contact": alertes.filter(section="Centre de contact", type="alerte"),
        "actions_contact": alertes.filter(section="Centre de contact", type="action"),
        "alertes_recl": alertes.filter(section="Réclamations", type="alerte"),
        "actions_recl": alertes.filter(section="Réclamations", type="action"),
        "data": data,
    })
