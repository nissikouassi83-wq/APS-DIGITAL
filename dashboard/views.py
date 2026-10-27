from collections import defaultdict
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from .models import Alerte, Contact, KpiGlobal, Reclamation, Semaine

INDICATEURS = [
    "DEMANDES D'INFORMATIONS",
    "ASSISTANCES e-CNPS",
    "RECLAMATIONS",
    "SUIVIS DE DOSSIERS",
    "INTERROMPUS/NON-RÉPONDUS",
]

LIBELLES_INDICATEURS = {
    "DEMANDES D'INFORMATIONS": "Demandes d'informations",
    "ASSISTANCES e-CNPS": "Assistances e-CNPS",
    "RECLAMATIONS": "Réclamations",
    "SUIVIS DE DOSSIERS": "Suivis de dossiers",
    "INTERROMPUS/NON-RÉPONDUS": "Interrompus / non-répondus",
}
ORDRE_INDICATEURS_EVOLUTION = (
    "DEMANDES D'INFORMATIONS",
    "ASSISTANCES e-CNPS",
    "RECLAMATIONS",
    "SUIVIS DE DOSSIERS",
)
MOIS_FR = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)


def _nombre(valeur):
    return f"{valeur:,}".replace(",", " ") if valeur is not None else "–"


def _indicateur_canonique(nom):
    if nom.startswith("INTERROMPUS/NON-R"):
        return "INTERROMPUS/NON-RÉPONDUS"
    return nom


def _variation(valeur, precedente, numero_precedent, favorable_si_baisse=False):
    if valeur is None or precedente is None:
        return "Comparaison non disponible", "neutre"
    difference = valeur - precedente
    signe = "+" if difference > 0 else ""
    if difference == 0:
        return f"stable vs S{numero_precedent}", "neutre"
    favorable = difference <= 0 if favorable_si_baisse else difference >= 0
    classe = "bon" if favorable else "mauvais"
    return f"{signe}{_nombre(difference)} vs S{numero_precedent}", classe


def _mois_rapport(periode, numero):
    fin_periode = periode.rsplit("-", 1)[-1].strip()
    try:
        date_fin = datetime.strptime(fin_periode, "%d/%m/%Y")
    except ValueError:
        return (9999, numero), f"S{numero} (date non disponible)"
    return (date_fin.year, date_fin.month), f"{MOIS_FR[date_fin.month - 1].capitalize()} {date_fin.year}"


@login_required
def index(request):
    semaines = list(Semaine.objects.order_by("numero"))
    if not semaines:
        return render(request, "dashboard/index.html", {"vide": True})

    kpis = {}
    kpis_par_semaine = defaultdict(dict)
    for ligne in KpiGlobal.objects.values(
        "semaine__numero", "indicateur"
    ).annotate(
        total=Sum("total"),
        appels=Sum("appels"),
        mails=Sum("mails"),
        messages=Sum("messages"),
    ):
        nom = _indicateur_canonique(ligne["indicateur"])
        if nom not in kpis:
            kpis[nom] = {"indicateur": nom, "total": 0, "appels": 0, "mails": 0, "messages": 0}
        for champ in ("total", "appels", "mails", "messages"):
            kpis[nom][champ] += ligne[champ] or 0
        kpis_par_semaine[ligne["semaine__numero"]][nom] = ligne

    contacts = defaultdict(lambda: [0, 0, 0, 0])
    contacts_par_semaine = defaultdict(lambda: [0, 0, 0, 0])
    for ligne in Contact.objects.values("semaine__numero", "motif").annotate(
        appels=Sum("appels"),
        mails=Sum("mails"),
        messages=Sum("messages"),
        total=Sum("total"),
    ):
        valeurs = [
            ligne["appels"] or 0,
            ligne["mails"] or 0,
            ligne["messages"] or 0,
            ligne["total"] or 0,
        ]
        for index, valeur in enumerate(valeurs):
            contacts[ligne["motif"]][index] += valeur
            contacts_par_semaine[ligne["semaine__numero"]][index] += valeur

    top = sorted(contacts.items(), key=lambda item: item[1][3], reverse=True)[:10]
    top_cinq = top[:5]
    top_huit = top[:8]
    top_appels = sorted(contacts.items(), key=lambda item: (-item[1][0], item[0]))[:8]
    top_messages = sorted(contacts.items(), key=lambda item: (-item[1][2], item[0]))[:8]
    mois_par_semaine = {}
    libelles_mois = {}
    for semaine in semaines:
        cle, libelle = _mois_rapport(semaine.periode, semaine.numero)
        mois_par_semaine[semaine.numero] = cle
        libelles_mois[cle] = libelle
    mois_ordonnes = sorted(libelles_mois)
    evolution_indicateurs = defaultdict(lambda: defaultdict(int))
    for numero, indicateurs in kpis_par_semaine.items():
        mois = mois_par_semaine[numero]
        for nom in ORDRE_INDICATEURS_EVOLUTION:
            if nom in indicateurs:
                evolution_indicateurs[nom][mois] += indicateurs[nom]["total"] or 0
    evolution_motifs = defaultdict(lambda: defaultdict(int))
    for ligne in Contact.objects.select_related("semaine").all():
        evolution_motifs[ligne.motif][mois_par_semaine[ligne.semaine.numero]] += ligne.total
    etiquettes_mois = [libelles_mois[cle] for cle in mois_ordonnes]

    total_contacts = kpis.get("TOTAL", {}).get("total") or 0
    canaux = [
        ("Appels", kpis.get("TOTAL", {}).get("appels") or 0),
        ("E-mails", kpis.get("TOTAL", {}).get("mails") or 0),
        ("WhatsApp + Messenger (cumulé)", kpis.get("TOTAL", {}).get("messages") or 0),
    ]
    canal_principal, volume_canal_principal = max(canaux, key=lambda item: item[1])
    motif_principal, volume_motif_principal = (
        (top[0][0], top[0][1][3]) if top else ("Aucun motif", 0)
    )
    resume = [
        {
            "label": "Moyenne de contacts par rapport",
            "valeur": _nombre(round(total_contacts / len(semaines))),
            "detail": f"Sur {len(semaines)} rapports importés",
        },
        {
            "label": "Canal le plus utilisé",
            "valeur": canal_principal,
            "detail": f"{_nombre(volume_canal_principal)} contacts sur la période",
        },
        {
            "label": "Motif le plus fréquent",
            "valeur": motif_principal,
            "detail": f"{_nombre(volume_motif_principal)} contacts sur la période",
        },
    ]
    motifs_complets = [
        {
            "motif": motif,
            "appels": _nombre(valeurs[0]),
            "mails": _nombre(valeurs[1]),
            "messages": _nombre(valeurs[2]),
            "total": _nombre(valeurs[3]),
        }
        for motif, valeurs in sorted(
            contacts.items(), key=lambda item: item[1][3], reverse=True
        )
    ]
    reclamations = list(Reclamation.objects.select_related("semaine").order_by("semaine__numero"))
    reclamations_par_semaine = {r.semaine.numero: r for r in reclamations}
    dernier_rapport = reclamations[-1] if reclamations else None
    total_recues = sum(r.recues or 0 for r in reclamations)
    total_resolues = sum(r.resolues or 0 for r in reclamations)

    numeros = list(range(semaines[0].numero, semaines[-1].numero + 1))
    numeros_importes = {semaine.numero for semaine in semaines}
    manquantes = [numero for numero in numeros if numero not in numeros_importes]
    recap_semaines = []
    recap_backlog = []
    weekly_channels = {"Appels": [], "E-mails": [], "Messages": []}
    weekly_indicators = {
        LIBELLES_INDICATEURS[nom]: [] for nom in ORDRE_INDICATEURS_EVOLUTION
    }
    weekly_claims = {"Réclamations reçues": [], "Réclamations résolues": [], "Dossiers en attente": []}
    for numero in numeros:
        semaine = next((s for s in semaines if s.numero == numero), None)
        if semaine is None:
            recap_semaines.append({"numero": numero, "absent": True})
            recap_backlog.append({"numero": numero, "absent": True})
            for values in (*weekly_channels.values(), *weekly_indicators.values(), *weekly_claims.values()):
                values.append(None)
            continue

        lignes_kpi = kpis_par_semaine[numero]
        total_kpi = lignes_kpi.get("TOTAL", {})
        contacts_semaine = contacts_par_semaine.get(numero, [0, 0, 0, 0])
        appels = (total_kpi.get("appels") or 0) if total_kpi else contacts_semaine[0]
        mails = (total_kpi.get("mails") or 0) if total_kpi else contacts_semaine[1]
        messages = (total_kpi.get("messages") or 0) if total_kpi else contacts_semaine[2]
        total_semaine = (total_kpi.get("total") or 0) if total_kpi else contacts_semaine[3]
        reclamation = reclamations_par_semaine.get(numero)
        if reclamation:
            recap_backlog.append({
                "numero": numero,
                "recu": _nombre(reclamation.backlog_recues),
                "en_cours": _nombre(reclamation.backlog_en_cours),
                "resolu": _nombre(reclamation.backlog_resolues),
                "hors_delai": _nombre(reclamation.hors_delai_25j),
            })
        else:
            recap_backlog.append({"numero": numero, "absent": True})
        valeurs = {
            "numero": numero,
            "appels": appels,
            "mails": mails,
            "messages": messages,
            "contacts": total_semaine,
            "informations": lignes_kpi.get("DEMANDES D'INFORMATIONS", {}).get("total"),
            "ecnps": lignes_kpi.get("ASSISTANCES e-CNPS", {}).get("total"),
            "reclamations_recues": reclamation.recues if reclamation else None,
            "reclamations_resolues": reclamation.resolues if reclamation else None,
            "backlog": reclamation.backlog_en_cours if reclamation else None,
            "taux": reclamation.taux_resolution_pct if reclamation else None,
        }
        recap_semaines.append({
            "numero": numero,
            **{key: _nombre(value) for key, value in valeurs.items() if key != "numero"},
            "taux": f"{_nombre(valeurs['taux'])} %" if valeurs["taux"] is not None else "–",
        })
        weekly_channels["Appels"].append(appels)
        weekly_channels["E-mails"].append(mails)
        weekly_channels["Messages"].append(messages)
        for nom in ORDRE_INDICATEURS_EVOLUTION:
            if nom == "RECLAMATIONS":
                valeur = reclamation.recues if reclamation else None
            else:
                ligne = lignes_kpi.get(nom)
                valeur = ligne["total"] if ligne else None
            weekly_indicators[LIBELLES_INDICATEURS[nom]].append(valeur)
        weekly_claims["Réclamations reçues"].append(reclamation.recues if reclamation else None)
        weekly_claims["Réclamations résolues"].append(reclamation.resolues if reclamation else None)
        weekly_claims["Dossiers en attente"].append(reclamation.backlog_en_cours if reclamation else None)

    sommes_recap = {
        "appels": kpis.get("TOTAL", {}).get("appels") or 0,
        "mails": kpis.get("TOTAL", {}).get("mails") or 0,
        "messages": kpis.get("TOTAL", {}).get("messages") or 0,
        "contacts": total_contacts,
        "informations": kpis.get("DEMANDES D'INFORMATIONS", {}).get("total") or 0,
        "ecnps": kpis.get("ASSISTANCES e-CNPS", {}).get("total") or 0,
        "reclamations_recues": total_recues,
        "reclamations_resolues": total_resolues,
    }
    pied_recap = {"numero": "Cumul", "backlog": "–", "taux": "–"}
    pied_recap.update({key: _nombre(value) for key, value in sommes_recap.items()})

    rapports_avec_contacts = [
        ligne for ligne in recap_semaines if not ligne.get("absent")
    ]
    dernier_numero = dernier_rapport.semaine.numero if dernier_rapport else semaines[-1].numero
    precedent = rapports_avec_contacts[-2] if len(rapports_avec_contacts) > 1 else None
    dernier_kpi = kpis_par_semaine[dernier_numero].get("TOTAL", {})
    dernier_contacts = dernier_kpi.get("total") or 0
    dernier_backlog = dernier_rapport.backlog_en_cours if dernier_rapport else None
    delta_contacts, classe_contacts = _variation(
        dernier_contacts,
        int(precedent["contacts"].replace(" ", "")) if precedent else None,
        precedent["numero"] if precedent else None,
        favorable_si_baisse=True,
    )
    delta_backlog, classe_backlog = _variation(
        dernier_backlog,
        int(precedent["backlog"].replace(" ", "")) if precedent and precedent["backlog"] != "–" else None,
        precedent["numero"] if precedent else None,
        favorable_si_baisse=True,
    )
    semaine_39 = reclamations_par_semaine.get(39)
    delta_backlog_s39, _ = _variation(
        dernier_backlog,
        semaine_39.backlog_en_cours if semaine_39 else None,
        39 if semaine_39 else None,
        favorable_si_baisse=True,
    )
    delta_taux, classe_taux = _variation(
        dernier_rapport.taux_resolution_pct if dernier_rapport else None,
        int(precedent["taux"].replace(" %", "")) if precedent and precedent["taux"] != "–" else None,
        precedent["numero"] if precedent else None,
    )
    contacts_precedents = int(precedent["contacts"].replace(" ", "")) if precedent else None
    variation_contacts = (
        round((dernier_contacts - contacts_precedents) * 100 / contacts_precedents)
        if contacts_precedents else None
    )
    contacts_detail = delta_contacts
    if variation_contacts is not None:
        contacts_detail = f"{delta_contacts} ({variation_contacts:+d} %)"
    cartes = [
        {"label": "Contacts reçus (cumul)", "valeur": _nombre(total_contacts), "detail": f"{len(semaines)} semaines"},
        {"label": "Réclamations reçues (cumul)", "valeur": _nombre(total_recues), "detail": f"{len(semaines)} semaines"},
        {"label": f"Contacts S{dernier_numero}", "valeur": _nombre(dernier_contacts), "detail": delta_contacts, "classe": classe_contacts},
        {"label": "Moyenne hebdomadaire", "valeur": _nombre(round(total_contacts / len(semaines))), "detail": "contacts par semaine"},
        {"label": "Dossiers en attente de traitement", "valeur": _nombre(dernier_backlog), "detail": delta_backlog, "classe": classe_backlog},
        {"label": "Taux de résolution", "valeur": f"{_nombre(dernier_rapport.taux_resolution_pct)} %" if dernier_rapport else "–", "detail": delta_taux, "classe": classe_taux},
    ]

    alertes_par_numero = defaultdict(list)
    for ligne in Alerte.objects.filter(type="alerte").values(
        "semaine__numero", "texte"
    ).order_by("semaine__numero", "id"):
        alertes_par_numero[ligne["semaine__numero"]].append(ligne["texte"])
    points_alerte_hebdomadaires = [
        {
            "numero": semaine.numero,
            "alertes": alertes_par_numero[semaine.numero],
        }
        for semaine in reversed(semaines)
    ]
    donnees_a_surveiller = []
    if dernier_rapport:
        donnees_a_surveiller.append(
            f"Dossiers en attente de traitement : {_nombre(dernier_backlog)}, {delta_backlog_s39.lower()}."
        )
        donnees_a_surveiller.append(
            f"Contacts : {_nombre(dernier_contacts)}, {contacts_detail.lower()}."
        )
        donnees_a_surveiller.append(
            f"Réclamations hors délai (plus de 25 jours) : {_nombre(dernier_rapport.hors_delai_25j)}."
        )

    alertes = defaultdict(lambda: defaultdict(dict))
    alertes_frequentes = {}
    for ligne in Alerte.objects.values("section", "type", "texte", "semaine__numero"):
        groupe = alertes[ligne["section"]][ligne["type"]]
        item = groupe.setdefault(ligne["texte"], {"texte": ligne["texte"], "semaines": set(), "occurrences": 0})
        item["semaines"].add(ligne["semaine__numero"])
        item["occurrences"] += 1
        if ligne["type"] == "alerte":
            frequent = alertes_frequentes.setdefault(
                ligne["texte"], {"texte": ligne["texte"], "semaines": set(), "occurrences": 0}
            )
            frequent["semaines"].add(ligne["semaine__numero"])
            frequent["occurrences"] += 1

    points_alerte_frequents = []
    for item in sorted(
        alertes_frequentes.values(),
        key=lambda item: (-item["occurrences"], item["texte"]),
    )[:5]:
        points_alerte_frequents.append({
            "texte": item["texte"],
            "occurrences": item["occurrences"],
            "semaines": ", ".join(f"S{numero}" for numero in sorted(item["semaines"])),
        })

    alertes_synthese = {}
    for section in ("Centre de contact", "Réclamations"):
        alertes_synthese[section] = {}
        for type_ in ("alerte", "action"):
            items = list(alertes[section][type_].values())
            for item in items:
                item["semaines"] = ", ".join(f"S{n}" for n in sorted(item["semaines"]))
            alertes_synthese[section][type_] = sorted(
                items, key=lambda item: (-item["occurrences"], item["texte"])
            )[:5]

    data = {
        "canaux": {
            "labels": [label for label, _ in canaux],
            "valeurs": [value for _, value in canaux],
        },
        "indicateurs": {
            LIBELLES_INDICATEURS[nom]: kpis[nom]["total"] or 0
            for nom in ORDRE_INDICATEURS_EVOLUTION
            if nom in kpis
        },
        "top_motifs": {
            "motifs": [motif for motif, _ in top],
            "appels": [valeurs[0] for _, valeurs in top],
            "mails": [valeurs[1] for _, valeurs in top],
            "messages": [valeurs[2] for _, valeurs in top],
        },
        "top_appels": {
            "motifs": [motif for motif, _ in top_appels],
            "valeurs": [valeurs[0] for _, valeurs in top_appels],
        },
        "top_messages": {
            "motifs": [motif for motif, _ in top_messages],
            "valeurs": [valeurs[2] for _, valeurs in top_messages],
        },
        "hebdomadaire": {
            "labels": [f"S{numero}" for numero in numeros],
            "canaux": weekly_channels,
            "indicateurs": weekly_indicators,
            "reclamations": weekly_claims,
        },
        "evolution": {
            "mois": etiquettes_mois,
            "indicateurs": {
                LIBELLES_INDICATEURS[nom]: [
                    evolution_indicateurs[nom].get(cle) for cle in mois_ordonnes
                ]
                for nom in INDICATEURS
                if nom in kpis
            },
            "motifs": {
                motif: [
                    evolution_motifs[motif].get(cle, 0) for cle in mois_ordonnes
                ]
                for motif, _ in top_cinq
            },
        },
        "reclamations": {
            "labels": ["Reçues", "Résolues"],
            "valeurs": [total_recues, total_resolues],
            "attente_labels": ["Dossiers en attente", "Dossiers traités", "En attente depuis plus de 25 jours"],
            "backlog_valeurs": [
                dernier_rapport.backlog_en_cours or 0,
                dernier_rapport.backlog_resolues or 0,
                dernier_rapport.hors_delai_25j or 0,
            ] if dernier_rapport else [0, 0, 0],
        },
    }

    return render(request, "dashboard/index.html", {
        "vide": False,
        "cartes": cartes,
        "nombre_rapports": len(semaines),
        "semaine_debut": semaines[0].numero,
        "semaine_fin": semaines[-1].numero,
        "periode_debut": semaines[0].periode,
        "periode_fin": semaines[-1].periode,
        "nombre_semaines": len(numeros),
        "semaines_manquantes": manquantes,
        "dernier_numero": dernier_numero,
        "resume": resume,
        "recap_semaines": recap_semaines,
        "recap_backlog": recap_backlog,
        "pied_recap": pied_recap,
        "points_alerte_hebdomadaires": points_alerte_hebdomadaires,
        "points_alerte_frequents": points_alerte_frequents,
        "donnees_a_surveiller": donnees_a_surveiller,
        "motifs_complets": motifs_complets,
        "motif_principal": motif_principal,
        "volume_motif_principal": _nombre(volume_motif_principal),
        "alertes_contact_synthese": alertes_synthese["Centre de contact"],
        "alertes_reclamations_synthese": alertes_synthese["Réclamations"],
        "data": data,
    })
