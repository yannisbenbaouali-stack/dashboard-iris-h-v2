# IRIS MAP

Outil cartographique de prospection IRIS REP : foncier, investissement off market, location.
Pilote : Saint Pierre des Corps (INSEE 37233).

## Données

Toutes les données sont chargées dans Supabase (projet kkznkuwoxoxvapejzytv) par la base elle même, via l'extension `http` et des tâches `pg_cron`. Chaque tâche cron est limitée à 2 minutes, d'où un chargement par lots.

| Table | Source | Fonction |
|---|---|---|
| carto_parcelles | Cadastre, API Carto IGN | carto_ingest_parcelles(code) |
| carto_batiments | BDNB CSTB, avec propriétaires personnes morales DGFiP | carto_step_batiments(code), lots de 900 |
| carto_mutations | DVF géolocalisé, 2021 à 2025 | carto_ingest_dvf(code, annee) |
| carto_etablissements | API Recherche d'entreprises (SIRENE) | carto_ingest_sirene(code, page, nb_pages) |
| carto_zonage | Géoportail de l'Urbanisme, API Carto | carto_ingest_zonage(code), relance cron toutes les 15 minutes tant que vide |

Journal : `carto_ingestion_log`. Curseur des lots : `carto_ingestion_etat`.

L'API BDNB anonyme est limitée à 10 bâtiments par appel, 120 appels par minute et 10000 appels par mois. Une commune moyenne consomme environ 500 appels. Pour passer à l'échelle régionale, il faut une clé API BDNB gratuite ou l'import des fichiers départementaux.

## Priorités

Calcul par `carto_calcul_priorites(code)`, cron quotidien 4h20 UTC.

P1 : bâtiment industriel en zone d'activité. P2 : industriel hors zone d'activité, ou bâtiment cible en zone d'activité. P3 : autre bâtiment d'activité ou de bureaux de 100 m² et plus.

Industriel : usage BDNB industriel, entrepôt, agricole ou secondaire, ou établissement actif de NAF 05 à 33, 35 à 38, 41 à 43, 45, 46, 49 ou 52 sur la parcelle. Zone d'activité : zone PLU UX, UY, UI, UZ, AUX ou libellé mentionnant activités, économie, industrie, artisanat, logistique.

Saint Pierre des Corps au 8 octobre 2026 : 117 P1, 254 P2, 184 P3.

## Fonctions lues par la carte

carto_geojson_batiments, carto_geojson_zonage, carto_geojson_etablissements, carto_fiche_batiment, carto_stats. Accès réservé au rôle authenticated, RLS politique iris_auth_all.

## Page

`carto.html`, publiée à côté du dashboard sur Cloudflare Pages : https://dashboard-iris-h.pages.dev/carto.html. Dépôt par site-put dans le bucket dashboard-site, puis site-deploy. Elle réutilise la session du dashboard (localStorage `iris_h_tok` et `iris_h_cfg`, même origine).

Ajouter une commune : lancer les fonctions d'ingestion avec son code INSEE, puis ajouter l'option dans le sélecteur de `carto.html`.
