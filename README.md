# Veille Emploi Data — paquet de publication

Tableau de veille d’offres data, avec une base hébergée et une collecte planifiée.

## Architecture

- **GitHub Pages** sert gratuitement le site statique contenu dans `web/`.
- **Supabase / PostgreSQL** conserve les annonces et autorise la lecture publique uniquement.
- **GitHub Actions** collecte les annonces toutes les 8 heures et permet un lancement manuel.
- Les clés publiques Supabase peuvent apparaître dans le navigateur ; la clé secrète reste exclusivement dans les secrets GitHub.

## Sources actuellement prévues

Le collecteur interroge une fois par jour Remotive (catégorie data) et jusqu’à trois pages de l’API publique Arbeitnow, puis filtre les annonces Data, Analytics, BI, Science et Engineering. Les cartes affichent la source, l’employeur et le lien vers l’annonce d’origine. Remotive demande explicitement un lien vers son annonce et une attribution comme source ; le tableau conserve ces liens et affiche « Source : Remotive ».

Ces sources ne couvrent pas le marché entier. Arbeitnow est plutôt centré sur l’Europe ; l’éligibilité des offres à distance depuis le Bénin doit être confirmée annonce par annonce. Aucune collecte béninoise n’est activée : intégrer seulement des API ou flux dont l’utilisation et la republication sont autorisées. Pas d’aspiration automatique de pages HTML.

## Déploiement

1. Créer un projet Supabase et exécuter `supabase/schema.sql` dans son SQL Editor.
2. Dans `web/config.js`, remplacer `VOTRE-PROJET` et `VOTRE-CLE-PUBLISHABLE` avec l’URL et la clé **publishable** du projet. Cette clé est publique et limitée par les règles RLS du schéma.
3. Créer un dépôt GitHub dont la racine contient les fichiers de ce dossier. Dans **Settings → Secrets and variables → Actions**, ajouter `SUPABASE_URL` et `SUPABASE_SECRET_KEY`. Utiliser la clé **secret** serveur, jamais la clé publishable.
4. Dans **Settings → Pages** du dépôt GitHub, choisir **GitHub Actions** comme source. Le workflow `.github/workflows/deploy-pages.yml` publie le contenu de `web/` à chaque mise à jour de la branche `main`.
5. Lancer `Collecte des offres Data toutes les 8 heures` manuellement une première fois dans l’onglet Actions. Vérifier les journaux et les annonces dans Supabase ; ensuite le workflow se répète toutes les 8 heures sur la branche par défaut.
6. Ouvrir l’URL GitHub Pages affichée dans **Settings → Pages**. En option, configurer un domaine personnalisé.

La planification GitHub suit le fuseau UTC. Les lancements planifiés peuvent être retardés par la plateforme. La collecte échoue explicitement si aucune source ne répond, pour éviter de présenter une exécution vide comme réussie.

## Statuts et limites

Les nouvelles annonces sont marquées **À vérifier**. Une API peut indiquer qu’une annonce existe sans confirmer que l’employeur accepte encore les candidatures depuis le Bénin. Une annonce absente d’un flux n’est pas supprimée automatiquement : le lien et la date de collecte restent consultables ; il faut revalider l’ouverture sur la source.

La collecte automatique ne couvre pas encore le marché béninois. Les pistes locales vérifiées manuellement dans `web/index.html` restent affichées en complément des annonces de Supabase, même lorsque la base est configurée. Elles ne sont pas rafraîchies automatiquement : leur date et leur statut doivent être revérifiés régulièrement. Les annonces de la base continuent à être affichées même si aucune collecte locale n’a été configurée.

## Fichiers principaux

- `web/index.html` — tableau de bord et filtres.
- `web/config.js` — URL Supabase et clé publique.
- `web/_headers` — en-têtes de sécurité du site.
- `supabase/schema.sql` — table, index, droits et politique RLS.
- `collector/collect.py` — collecte, normalisation et dédoublonnage.
- `.github/workflows/daily-collect.yml` — programmation de la collecte.
- `.github/workflows/deploy-pages.yml` — publication du site sur GitHub Pages.
