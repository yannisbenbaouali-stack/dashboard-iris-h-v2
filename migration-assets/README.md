# Migration des visuels vers assets.irisrep.com

Sortir les visuels publiés des buckets Supabase `logos`, `visuels` et `dashboard-assets`
et les servir depuis https://assets.irisrep.com, hébergement OVH mutualisé
wbopwfv.cluster131, home `/assets`.

Motif : l'egress du projet Supabase kkznkuwoxoxvapejzytv a fait sauter le quota de
l'organisation, 14,19 Go constatés pour 5,5 Go en cible. Cycle de facturation ancré au 12.

## À exécuter depuis un poste avec accès réseau

Claude Desktop ou Cowork en local. La session Claude Code distante n'a aucune sortie
HTTPS vers assets.irisrep.com, supabase.co, api.ovh.com ni pages.dev.

Prérequis : `curl`, `jq`, ImageMagick (`magick` ou `convert`), `pngquant` en option.

```
cp .env.example .env      # remplir depuis la table outils Supabase
./assets-migration.sh ping
./assets-migration.sh inventaire
./assets-migration.sh export
./assets-migration.sh depot
./assets-migration.sh verif
./assets-migration.sh mapping
```

Tout le travail se fait dans `_travail/`, non versionné.

### ping
Interroge depot.php, actions `ping` puis `list`. Sert à savoir ce qui est déjà déposé
et à confirmer les noms de champs attendus par l'action `upload`. Si la réponse montre
d'autres noms que `file` et `path`, ajuster `DEPOT_CHAMP_FICHIER` et `DEPOT_CHAMP_CHEMIN`
dans `.env` avant l'étape depot.

### inventaire
Liste récursivement les trois buckets, écarte `_archives_originaux/` et produit
`_travail/manifest.tsv` : bucket, chemin source, chemin cible, taille.
Signale les collisions de noms cibles. À relire avant d'aller plus loin.

Règles de nommage appliquées : minuscules, sans accents, underscores et espaces en
tirets, arborescence conservée.

| Cible | Source |
|---|---|
| `sig/` | `logos/sig/` |
| `logos/<entite>/` | `logos/<entite>/` |
| `arristo/` | `visuels/arristo/` |
| `arristo/events/` | `dashboard-assets/events/` |
| `dashboard/logos/` | `dashboard-assets/logos/` |
| `electricien/riseup/` | `dashboard-assets/electricien/riseup/` |
| `docs/` | `dashboard-assets/dossiers/` et `dashboard-assets/iris_rep/` |

### export
Télécharge les sources depuis les URLs publiques Supabase, une seule fois, environ
25 Mo d'egress ponctuel, puis produit `_travail/out/`.

Les signatures `sig/*.png` sont redimensionnées à 200 px de large, métadonnées
retirées, quantifiées si pngquant est présent, et une alerte sort si le résultat
dépasse 50 Ko. `sig/bym-tce.png` fait 58 Ko aujourd'hui, il est concerné.

Les GIF animés ne sont pas copiés, ils sortent en alerte. Trois fichiers de
`dashboard-assets/electricien/riseup/` sont dans ce cas.

Un `.htaccess` est généré : cache immuable un an, CORS ouvert, index désactivé.

Drive reste le master des sources haute définition. Le téléchargement depuis les
buckets n'est qu'un raccourci pour récupérer les exports déjà publiés, pas une
nouvelle source de vérité.

### depot
Envoie `_travail/out/` sur l'hébergement par depot.php, un fichier par appel,
en conservant l'arborescence. Chaque échec est journalisé dans `_travail/journal.log`.

### verif
Contrôle chaque cible du manifest en HTTP, sort en erreur si une seule n'est pas en 200.
Ne pas passer à la suite tant que cette étape n'est pas propre.

### mapping
Produit `_travail/mapping.csv`, ancienne URL Supabase vers nouvelle URL assets.
C'est ce fichier qui pilote le remplacement.

## Remplacement des URLs, à faire à la main

1. **Signatures Gmail.** Paramètres Gmail, Signature, réinsérer l'image par URL.
   Aucune API de signature n'est exposée par le connecteur Gmail. Vérifier aussi la
   table `iris_templates`, colonne `contenu_base64`, qui peut contenir des gabarits
   d'emails avec les anciennes URLs.
2. **Dashboard.** Les pages HTML vivent dans le bucket privé `dashboard-site`.
   Télécharger, remplacer selon `mapping.csv`, redéposer, redéployer par wrangler.
3. **Sites Lovable**, workspace `itUTA2ri8c5ROdhihx0k` : ARRISTO, IRIS REAL ESTATE,
   BYM, UrbanRise, CentreVolt Électricité, SYNAY, Orleans Colocation Hub. Faire la
   substitution projet par projet, en une seule demande à l'agent Lovable.
4. **Supports ARRISTO** : cartons, bannières LinkedIn, emails de campagne.

## Contrôle avant de fermer les buckets

`./assets-migration.sh restes` donne la requête à passer sur les logs Supabase.
Tant qu'elle renvoie des appels sur `logos`, `visuels` ou `dashboard-assets`,
ne pas basculer les buckets en privé. Vérifier deux jours de suite, puis mesurer
l'egress avant de restreindre.

## Rappels

Un fichier publié ne change jamais de contenu. Une nouvelle version porte un suffixe
`v2`. Jamais de sous domaine fournisseur dans une URL publiée, ni supabase.co, ni
pages.dev, ni r2.dev. Aucun credential dans ce dépôt, tout vient de la table `outils`.
