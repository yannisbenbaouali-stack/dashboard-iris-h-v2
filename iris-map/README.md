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

## Fonctions lues par la carte web

carto_mvt(z,x,y) sert des tuiles vectorielles (bâtiments à partir du zoom 12, cibles seules sous le zoom 15, entreprises dès le zoom 15), environ 70 Ko par tuile. carto_recherche alimente l'explorateur, carto_fiche_batiment la fiche, carto_geojson_zonage la couche PLU chargée à la demande, carto_stats l'en-tête. Accès réservé au rôle authenticated, RLS politique iris_auth_all.

Suivi de prospection : colonnes statut_prospection, notes, date_dernier_contact, prochaine_action de carto_batiments, modifiables depuis la fiche web ou depuis QGIS.

## QGIS

`qgis/IRIS_MAP_QGIS.py`, à exécuter une fois dans la console Python de QGIS. Il crée le projet ~/Documents/IRIS_MAP.qgz connecté en direct à Supabase par l'utilisateur qgis_iris (mot de passe dans la table outils). Vues dédiées : v_qgis_batiments, v_qgis_etablissements, v_qgis_ventes. qgis_iris lit les tables carto et ne peut écrire que les quatre colonnes de suivi.

## Page

`carto.html`, publiée à côté du dashboard sur Cloudflare Pages : https://dashboard-iris-h.pages.dev/carto.html. Dépôt par site-put dans le bucket dashboard-site, puis site-deploy. Elle réutilise la session du dashboard (localStorage `iris_h_tok` et `iris_h_cfg`, même origine).

Ajouter une commune : lancer les fonctions d'ingestion avec son code INSEE, puis ajouter l'option dans le sélecteur de `carto.html`.

## Repérages

Table `carto_reperages` : zones et points dessinés dans QGIS (couches Repérages zones et Repérages points), visibles et modifiables (statut, contact, notes) sur la page web. Surface calculée automatiquement pour les zones.

## Propriétaires enrichis

Table `carto_proprietaires`, alimentée par `carto_enrichir_proprietaire(siren)` depuis l'API Recherche d'entreprises : nature juridique, dirigeants et années de naissance, effectif, finances. Vue `v_carto_cibles_p1` : propriétaires privés des bâtiments P1, hors acteurs publics, réseaux et grandes enseignes.

## PLU et PPRI

Pièces du PLU lues via la fonction relais `plu-fetch?url=` (liste blanche d'hôtes publics : Géoportail de l'Urbanisme, Géorisques, préfecture 37), texte extrait par pdftotext. Synthèses et règles dans `plu/37233`.

| Table | Contenu |
|---|---|
| carto_plu_regles | Règles par zone et secteur : destinations, emprise, hauteur, implantation, stationnement, lecture investisseur, pages |
| carto_plu_zones | Zonage GPU découpé au contour communal (`carto_calcul_plu_zones`) |
| carto_ppri, carto_ppri_zones | Zonage réglementaire PPRI Val de Tours, WFS Géo IDE DDT 37 (`carto_ingest_ppri`, `carto_calcul_ppri_zones`) |
| carto_ppri_regles | Règles PPRI par zone, plafonds d'emprise activité sous PHEC et totale |
| carto_communes | Contours communaux, geo.api.gouv.fr |

Carte : couches « PLU, zones et règles » (`carto_geojson_plu`) et « PPRI, zones inondables » (`carto_geojson_ppri`), rubrique « Urbanisme et capacité » de la fiche bâtiment (`carto_urba_batiment`). Plain pied = min(plafond sous PHEC, plafond total / 2), plafond le plus strict entre PLU et PPRI.

Méthode : skill `skills/expertise-urbanisme-plu/SKILL.md`, aussi dans la table skills.
