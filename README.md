# Flux RSS — Actualités Nîmes & Gard (hors Actu.fr)

Ce mini-projet fabrique et maintient à jour **automatiquement** un flux
RSS qui agrège les articles de presse concernant **Nîmes et le Gard**,
tous sujets et tous médias confondus, **à l'exception d'Actu.fr**.

## Comment ça marche

- `generate_feed.py` va chercher les articles récents via la recherche
  Google Actualités (`Nîmes OR Gard`, avec `-site:actu.fr`), qui agrège
  automatiquement des centaines de sources françaises (Midi Libre,
  Objectif Gard, France Bleu, France 3 Occitanie, La Provence, etc.).
- Il **filtre** les articles par pertinence (mot-clé Nîmes/Gard dans le
  titre ou le résumé), **exclut** toute source dont le lien ou le nom
  contient "actu.fr" (double sécurité, au cas où), **fusionne les
  doublons** (le même sujet repris par deux médias) et régénère un
  fichier `feed.xml` propre, trié du plus récent au plus ancien.
- Un **workflow GitHub Actions** (`.github/workflows/update-feed.yml`)
  relance ce script automatiquement **toutes les 15 minutes**, 24h/24,
  gratuitement, sans aucun serveur à gérer.

## Installation (10 minutes, une seule fois)

1. Créez un compte GitHub si vous n'en avez pas (gratuit) :
   https://github.com/signup
2. Créez un nouveau dépôt (repository), par exemple nommé
   `nimes-gard-rss`, en le laissant **public** (nécessaire pour la
   version gratuite de GitHub Pages).
3. Ajoutez-y les 3 fichiers de ce projet en conservant l'arborescence :
   ```
   generate_feed.py
   .github/workflows/update-feed.yml
   README.md
   ```
   (le plus simple : sur la page du dépôt, "Add file" → "Upload
   files", et glissez les 3 fichiers/dossiers).
4. Allez dans l'onglet **Settings → Pages** du dépôt, et sous "Build
   and deployment" choisissez **Source : Deploy from a branch**, puis
   **Branch : main / (root)**. Validez.
5. Allez dans l'onglet **Actions**, autorisez les workflows si demandé,
   puis lancez manuellement "Mise à jour du flux RSS Nîmes/Gard" via
   **Run workflow** (sinon il se lancera de lui-même dans les 15
   minutes suivant sa première programmation).
6. Une fois l'action terminée (icône verte), votre flux est en ligne à
   l'adresse :
   ```
   https://VOTRE-PSEUDO.github.io/nimes-gard-rss/feed.xml
   ```

## Utilisation

Collez cette URL dans n'importe quel lecteur RSS : Feedly, Inoreader,
NetNewsWire, Fluent Reader, ou l'agrégateur intégré de votre
navigateur/téléphone. Le lecteur ira relire le flux à son propre
rythme ; comme `feed.xml` est régénéré toutes les 15 minutes côté
serveur, un nouvel article apparaît généralement dans l'heure suivant
sa parution — souvent bien plus vite.

## Pour aller plus loin

- **Ajouter des médias en plus de Google Actualités** : ouvrez le site
  d'un média local, affichez son code source (`Ctrl+U`) et cherchez
  `application/rss+xml`, ou essayez `<site>/feed` ou `<site>/rss`.
  Ajoutez ensuite l'URL trouvée dans la liste `SOURCES` en haut de
  `generate_feed.py`.
- **Exclure d'autres médias** : ajoutez leur domaine dans la liste
  `EXCLUDED_DOMAINS`.
- **Changer la fréquence de mise à jour** : modifiez la ligne `cron`
  dans `.github/workflows/update-feed.yml` (attention : GitHub Actions
  déconseille un cron plus fréquent que toutes les 5 minutes).
- **Élargir/resserrer la fenêtre temporelle** : le `when:2d` dans
  l'URL Google Actualités peut devenir `when:1d`, `when:7d`, etc.

## Sans GitHub (alternative locale)

Vous pouvez aussi exécuter `python3 generate_feed.py` vous-même sur
votre ordinateur (planifié via le Planificateur de tâches Windows ou
`cron` sur Mac/Linux), puis héberger le fichier `feed.xml` généré sur
n'importe quel espace web statique, ou simplement l'ouvrir en local
dans un lecteur RSS qui accepte les fichiers.
