# SHA APS DIGITALE – Tableau de bord hebdomadaire

Projet Django qui lit les rapports hebdomadaires `.pptx` (centre de contact + réclamations)
et affiche un tableau de bord interactif (Plotly).

## Démarrage dans VS Code

1. **Fichier > Ouvrir un dossier…** et choisir `sha_dashboard`.
2. Ouvrir un terminal (`Ctrl+ù` ou *Terminal > Nouveau terminal*) puis :

```bash
python -m venv .venv
# Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# Windows (cmd) : .venv\Scripts\activate.bat      |  Mac/Linux : source .venv/bin/activate

pip install -r requirements.txt
python manage.py makemigrations dashboard
python manage.py migrate
python manage.py import_pptx
python manage.py runserver
```

3. Ouvrir http://127.0.0.1:8000 (internet requis : Plotly se charge depuis un CDN).

Si VS Code propose de choisir un interpréteur Python, prenez celui du dossier `.venv`.
Vous pouvez aussi lancer avec **F5** (menu *Exécuter et déboguer* > « Django : lancer le dashboard »).

## Déploiement sur Vercel

Pour créer un nouveau projet, importez le dépôt GitHub `nissikouassi83-wq/APS-DIGITAL` dans Vercel et sélectionnez la branche `main`. Dans les variables d'environnement du projet, ajoutez `DJANGO_SECRET_KEY` avec une clé Django générée localement. Gardez cette clé secrète : ne la mettez pas dans le code ni sur GitHub. Laissez les variables système Vercel activées afin que Django reconnaisse le domaine du déploiement. Après avoir ajouté la clé, lancez le déploiement.

## Chaque semaine

1. Déposer le nouveau fichier dans `data/pptx/` (le nom doit contenir `Sem_NN`, ex. `SHA_APS_DIGITALE_Sem_43.pptx`).
2. `python manage.py import_pptx` (réimporter ne crée pas de doublons).
3. Rafraîchir la page.

Les rapports `.pptx` et la base de données locale ne sont pas inclus dans le dépôt public. Ajoutez vos rapports localement dans `data/pptx/` avant de lancer l'import.

## Structure

```
sha_dashboard/
├── manage.py
├── requirements.txt
├── data/pptx/                  <- rapports hebdo (.pptx)
├── config/                     <- réglages Django (settings.py, urls.py)
├── dashboard/
│   ├── models.py               <- tables : Semaine, Contact, KpiGlobal, Reclamation, Alerte
│   ├── views.py                <- calcul des indicateurs pour la page
│   ├── services/extraction.py  <- lecture des .pptx (testable seul)
│   ├── management/commands/import_pptx.py
│   └── templates/dashboard/index.html   <- page + graphiques Plotly
└── .vscode/                    <- config VS Code (F5, extensions)
```

## Tester l'extraction seule

```bash
python -m dashboard.services.extraction data/pptx/SHA_APS_DIGITALE_Sem_42.pptx
```

## Administration (optionnel)

```bash
python manage.py createsuperuser
```
puis http://127.0.0.1:8000/admin pour consulter/corriger les données.

## Limites connues

- La semaine 40 n'est pas dans les fichiers : les graphiques affichent S38, S39, S41, S42.
- Les variantes d'orthographe des motifs sont harmonisées dans `NORMALISATION`
  (`dashboard/services/extraction.py`) : ajoutez-y les nouvelles variantes rencontrées.
