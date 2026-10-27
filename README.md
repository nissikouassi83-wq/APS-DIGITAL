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

Le tableau de bord exige une connexion. La page d’accueil redirige les visiteurs non connectés vers `/connexion/`. Créez les comptes autorisés avec `python manage.py create_dashboard_user` ; cette commande crée un compte de consultation sans accès à l’administration. Les utilisateurs connectés peuvent changer leur mot de passe depuis le lien « Mot de passe » dans l’en-tête.

Vercel doit utiliser une base PostgreSQL persistante. Ajoutez une intégration PostgreSQL compatible, puis configurez `DATABASE_URL` et `DJANGO_SECRET_KEY` dans les variables d’environnement Vercel. Gardez ces valeurs secrètes et ne les mettez jamais dans GitHub. `DATABASE_URL` est obligatoire sur Vercel : le déploiement échoue volontairement si elle manque, au lieu de démarrer avec une base SQLite éphémère. Laissez les variables système Vercel activées afin que Django reconnaisse le domaine du déploiement.

Pour transférer les données locales vers une base PostgreSQL vide :

1. Depuis la base SQLite locale, exportez les données avec `python manage.py dumpdata dashboard --indent 2 --output private-dashboard-data.json`.
2. Configurez temporairement `DATABASE_URL` dans votre terminal avec l’URL de la base PostgreSQL Vercel ; ne la mettez pas dans un fichier suivi par Git.
3. Lancez `python manage.py migrate` puis `python manage.py loaddata private-dashboard-data.json`.
4. Créez le compte de consultation sur cette même base avec `python manage.py create_dashboard_user`.
5. Supprimez le fichier de transfert après l’import. Il est exclu de Git par `.gitignore`.

Les rapports PowerPoint, la base SQLite et les mots de passe ne doivent pas être ajoutés au dépôt. Une fois la base et ses comptes prêts, déployez la branche `main` depuis Vercel.

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
