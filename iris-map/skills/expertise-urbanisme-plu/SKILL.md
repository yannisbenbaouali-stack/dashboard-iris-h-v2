---
name: expertise-urbanisme-plu
description: Lire, analyser et interpréter un document d'urbanisme français (PLU, PLUi, PLUi H D, PADD, OAP, PSMV, SPR, carte communale, RNU) et les servitudes qui s'y superposent (PPRI, PPRT, SUP, ABF), pour dire ce qu'on peut construire, étendre, reconvertir ou densifier sur une parcelle ou une zone, et en tirer une lecture investisseur en immobilier d'entreprise (activité, logistique, bureaux). À utiliser dès qu'une question porte sur une zone PLU, une règle d'urbanisme, une étude de capacité, une faisabilité, un changement de destination, ou l'ajout d'une commune dans IRIS MAP.
version: 1
agents: [claude]
categorie: expertise
---

# Expertise urbanisme, interprétation des PLU, PLUi, PADD, OAP, PSMV

## 1. Principe

Un document d'urbanisme ne se lit jamais seul. La constructibilité réelle d'un terrain est l'intersection de cinq couches, et c'est toujours la règle la plus contraignante qui s'applique :

1. Le règlement du document local (PLU, PLUi, PSMV, carte communale ou à défaut RNU), écrit et graphique, en conformité.
2. Les OAP, en compatibilité (esprit et principes, pas la lettre), et le PADD qui n'est pas opposable mais annonce les évolutions.
3. Les servitudes d'utilité publique annexées : PPRI, PPRT, PPRN, monuments historiques et abords (ABF), AC, EL, I3 gaz, T1 voies ferrées, PT, aéronautiques. Elles s'imposent au PLU.
4. Les prescriptions graphiques : emplacements réservés, EBC, patrimoine L151 19 et L151 23, périmètres d'attente de projet L151 41 5°, linéaires commerciaux, secteurs de mixité, marges de recul, plans de masse.
5. Les règles nationales et périmètres d'information : ZAC, DPU et DPU renforcé, ZAD, secteurs bruit, PEB, Loi Barnier L111 6 (75 ou 100 m hors agglomération), RE2020, ZAN, raccordement aux réseaux de chaleur classés, ICPE.

Ne jamais conclure sur une parcelle sans avoir croisé ces cinq couches. Dire explicitement quelles couches n'ont pas pu être vérifiées.

## 2. Récupérer le document en vigueur

1. Identifier le document : API Carto GPU `https://apicarto.ign.fr/api/gpu/document?geom=` (point GeoJSON) donne `gpu_doc_id`, type, date. Pour un PLUi, la partition est `DU_<SIREN EPCI>`.
2. Lister les pièces : `https://www.geoportail-urbanisme.gouv.fr/api/document/<gpu_doc_id>/files`, puis télécharger `/files/<nom>`. Depuis IRIS, passer par la fonction relais Supabase `plu-fetch?url=` (liste blanche d'hôtes publics), puis `pdftotext -layout`.
3. Zonage vecteur : `apicarto gpu/zone-urba`, prescriptions `gpu/prescription-surf`, `-lin`, `-pct`, servitudes `gpu/assiette-sup-s`. Les PPR détaillés sont souvent seulement en enveloppe dans le GPU : chercher le zonage réglementaire sur data.gouv.fr ou le WFS Géo IDE de la DDT (couche `N_ZONE_REG_PPRN_<id>_S_<dpt>`, attention à l'ordre lat lon en EPSG 4326 WFS 1.1).
4. Vérifier la version : lire la note de procédure. Distinguer révision (change le PADD), modification (règlement, OAP), modification simplifiée, mise en compatibilité (DUP, déclaration de projet), mise à jour (annexes seulement, ne change aucune règle). Repérer une révision en cours : sursis à statuer possible dès le débat sur le PADD.
5. Si le règlement et les OAP n'ont pas la même date, vérifier si les OAP ont été modifiées.

## 3. Lire le règlement écrit

Deux structures coexistent.

Ancienne structure, 14 articles (PLU antérieurs au décret du 28 décembre 2015 ou n'ayant pas opté) : art. 1 interdictions, 2 conditions, 3 accès voirie, 4 réseaux, 5 superficie minimale (abrogé ALUR), 6 implantation voies, 7 limites séparatives, 8 sur une même propriété, 9 emprise au sol, 10 hauteur, 11 aspect, 12 stationnement, 13 espaces libres et plantations, 14 COS (abrogé ALUR).

Nouvelle structure, trois chapitres : I destinations et usages (interdictions, limitations, mixité), II caractéristiques urbaines, architecturales, environnementales et paysagères (volumétrie, implantation, emprise, hauteur, qualité, biotope, stationnement), III équipements et réseaux.

Pour chaque zone et secteur, remplir la grille :

1. Vocation, rappel du rapport de présentation.
2. Destinations et sous destinations : autorisée, sous conditions, interdite. Nouvelle nomenclature R151 27 et R151 28 : exploitation agricole et forestière ; habitation (logement, hébergement) ; commerce et activités de service (artisanat et commerce de détail, restauration, commerce de gros, activités de services avec accueil de clientèle, cinéma, hôtels, autres hébergements touristiques) ; équipements d'intérêt collectif et services publics ; autres activités des secteurs primaire, secondaire ou tertiaire (industrie, entrepôt, bureau, centre de congrès et d'exposition, cuisine dédiée à la vente en ligne). Si le PLU utilise l'ancienne liste (habitation, hébergement hôtelier, bureaux, commerce, artisanat, industrie, exploitation agricole, entrepôt, CINASPIC), faire la correspondance et le signaler comme interprétation.
3. Logique d'écriture : « tout ce qui n'est pas interdit à l'article 1 est autorisé » ou « seul ce qui est listé à l'article 2 est admis ». Le dire.
4. Emprise au sol en pourcentage et assiette de calcul (unité foncière, terrain après déduction des espaces protégés), définition locale du lexique ou R420 1 (projection verticale, débords inclus ou non).
5. Hauteur : point de mesure (sol naturel, égout, faîtage, acrotère), plafond en mètres et en niveaux, règles de prospect.
6. Implantations : voies (alignement ou recul), limites séparatives (en limite, retrait H/2 avec minimum), entre bâtiments.
7. Pleine terre, espaces verts, coefficient de biotope.
8. Stationnement par destination : en places par m² de surface de plancher ou en pourcentage de surface. Le stationnement est souvent le vrai plafond économique des bureaux.
9. Aspect, toitures, clôtures, matériaux interdits.
10. Réseaux, eaux pluviales, gestion à la parcelle.
11. Exceptions : existant non conforme, extensions limitées en m² ou en %, équipements publics, date de référence de l'existant.

Toujours consulter le lexique : la définition locale d'emprise, de hauteur, d'annexe, d'extension, de surface de plancher prime sur l'intuition.

## 4. PADD, OAP, PSMV, SPR

PADD : non opposable aux autorisations, mais c'est la feuille de route politique. Repérer les secteurs dits à muter, à densifier, à protéger, les zones d'activités confortées ou reconverties. Un secteur d'activité que le PADD veut faire muter vers le logement est un risque pour un utilisateur et une opportunité de valorisation foncière pour un investisseur patient.

OAP : opposables en compatibilité. Lire la programmation (nombre de logements, surfaces d'activités, phasage), les principes de desserte, les espaces verts imposés, l'obligation d'opération d'ensemble. Une OAP sans activité sur une zone 1AU ferme la porte à l'immobilier d'entreprise.

PSMV : document de l'État qui remplace le PLU dans le secteur sauvegardé (devenu SPR). Lecture immeuble par immeuble selon la légende : immeuble protégé à conserver, immeuble pouvant être conservé ou remplacé, immeuble à démolir ou modifier, espaces libres protégés, emprises constructibles. Avis conforme de l'ABF. PVAP (plan de valorisation de l'architecture et du patrimoine) : servitude, règles patrimoniales superposées au PLU.

PLUi : même lecture, mais vérifier les plans de secteur communaux, les règles communes en tête de règlement et les annexes par commune. Les PLUi H incluent un POA habitat, les PLUi D un POA mobilités.

## 5. Risques et servitudes, réflexes

PPRI : déterminer la zone réglementaire de la parcelle (aléa et enjeu), puis lire emprise au sol maximale, indice ou plafond de surface de plancher, cote de plancher au dessus des PHEC, interdiction de sous sols, règles d'extension de l'existant à la date de référence, changement de destination vers plus ou moins de vulnérabilité. Une ZDE (zone de dissipation d'énergie derrière une digue) est en pratique inconstructible pour du neuf.

PPRT : zones rouges, bleues, de recommandation ; interdiction d'ERP et d'habitat en général ; prescriptions de confinement.

Abords monuments historiques (500 m ou périmètre délimité) : avis de l'ABF, conforme en covisibilité.

Servitude I3 gaz, I4 électricité, T1 voie ferrée, PT radio : distances et consultations obligatoires.

## 6. Interprétation investisseur immobilier d'entreprise

Pour chaque zone, produire une lecture en 3 à 5 phrases, sans tirets :

1. Ce qu'on peut y faire en activité, logistique, bureaux, et sous quelles conditions.
2. Le plafond réel de constructibilité : emprise PLU ou PPR, hauteur, stationnement, pleine terre. Calcul de capacité théorique : SP max ≈ min(emprise PLU, emprise PPR) × terrain × nombre de niveaux permis par la hauteur, puis réduite par stationnement et espaces verts imposés.
3. Le sens de l'histoire : PADD, OAP, procédures en cours, périmètres d'attente.
4. Les pièges : patrimoine, ER, EBC, PPRT, droit de préemption, linéaires.
5. Le verdict opérationnel : cible d'acquisition, de reconversion, de densification, ou à éviter.

Ordre de hauteur utile : logistique classe A 10 à 12 m sous poutre, soit 13 à 15 m au faîtage ; activité PME 7 à 9 m ; bureaux R+2 à R+4.

## 7. Restitution

1. Table Supabase `carto_plu_regles` : une ligne par zone ou secteur et par commune, colonnes de la grille, `lecture_iris`, `pages`, `source_doc`, `date_doc`. Jointure avec `carto_zonage.libelle`.
2. Si PPR : table `carto_ppri` (zones réglementaires) et `carto_ppri_regles`.
3. Carte IRIS MAP : couche PLU colorée par famille de zone, info bulle avec destinations, emprise, hauteur, stationnement, lecture investisseur.
4. Note d'analyse en Google Doc dans le dossier Prospection, ligne documents_claude.
5. Citer systématiquement la page du règlement. Distinguer ce qui est écrit, ce qui est interprété, ce qui reste à confirmer auprès du service instructeur. Sécuriser une opération par un certificat d'urbanisme opérationnel (CUb) ou un rendez vous avec l'instructeur avant toute offre.

## 8. Erreurs à ne pas commettre

1. Prendre le zonage GPU pour le seul critère : une zone U peut être en ZDE de PPRI et donc inconstructible.
2. Confondre conformité (règlement) et compatibilité (OAP).
3. Lire un plafond d'emprise sans son assiette de calcul ou sa date de référence.
4. Oublier le stationnement, qui tue souvent les bilans de bureaux.
5. Supposer qu'une mise à jour de PLU a changé les règles : elle ne touche que les annexes.
6. Ignorer une révision en cours et le sursis à statuer.
7. Inventer une règle absente : écrire « le règlement ne fixe pas de règle » et le signaler.
