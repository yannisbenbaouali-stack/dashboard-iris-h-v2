# IRIS MAP, projet QGIS de prospection IRIS REP
# Usage : QGIS 3.28 ou plus, menu Extensions > Console Python > Afficher l'éditeur,
# ouvrir ce fichier, cliquer sur Exécuter. Le mot de passe de l'utilisateur qgis_iris
# est dans l'onglet Outils du dashboard, fiche "Supabase QGIS, accès base cartographie IRIS MAP".
# Il est stocké chiffré dans le gestionnaire d'authentification QGIS, jamais dans le projet.

import os
from urllib.parse import quote
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsDataSourceUri, QgsApplication, QgsAuthMethodConfig,
    QgsCoordinateReferenceSystem, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol,
    QgsWkbTypes, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsEditorWidgetSetup,
    QgsAction, QgsFillSymbol, QgsMarkerSymbol, QgsLayerTreeGroup, QgsCoordinateTransform, QgsRectangle,
)
from qgis.PyQt.QtWidgets import QInputDialog, QLineEdit, QMessageBox
from qgis.PyQt.QtGui import QColor, QFont
from qgis.utils import iface

REF = 'kkznkuwoxoxvapejzytv'
ROLE = 'qgis_iris'
HOTES = [
    ('aws-0-eu-west-1.pooler.supabase.com', f'{ROLE}.{REF}'),
    ('aws-1-eu-west-1.pooler.supabase.com', f'{ROLE}.{REF}'),
    (f'db.{REF}.supabase.co', ROLE),
]
AUTH_NOM = 'IRIS MAP Supabase'
PROJET = os.path.join(os.path.expanduser('~'), 'Documents', 'IRIS_MAP.qgz')
STATUTS = ['À contacter', 'Contacté', 'Rendez vous', 'Mandat vendeur', 'Mandat recherche', 'À vendre', 'Pas vendeur', 'À revoir', 'Écarté']
TYPES_REP = ['Terrain nu', 'Bâtiment vacant', 'Panneau à vendre', 'Panneau à louer', 'Friche', 'Périmètre de prospection', 'Autre']
STATUTS_REP = ['À qualifier', 'Propriétaire identifié', 'Contacté', 'Mandat', 'Écarté']


def PUBLIQUES(GR, GPF):
    return [
        ('Urbanisme', 'sup', "Servitudes d'utilité publique", 'wms', GPF),
        ('Urbanisme', 'prescription', 'Prescriptions du PLU', 'wms', GPF),
        ('Urbanisme', 'info', 'Informations du PLU', 'wms', GPF),
        ('Foncier', 'BDTOPO-DIFF-ZONE_ACTIVITES', "Zones d'activités (BD TOPO)", 'wmts', 'PM_7_18|normal|image/png'),
        ('Foncier', 'POTENTIEL.SOLAIRE.FRICHE', 'Friches recensées', 'wms', GPF),
        ('Risques', 'PPRN_ZONE_INOND', 'PPR inondation, zonage réglementaire', 'wms', GR),
        ('Risques', 'ALEA_SYNT_01_02MOY', 'Zones inondables, crue centennale', 'wms', GR),
        ('Risques', 'REMNAPPE', 'Remontées de nappes', 'wms', GR),
        ('Risques', 'ALEARG_REALISE', 'Retrait gonflement des argiles', 'wms', GR),
        ('Risques', 'CAVITE_LOCALISEE', 'Cavités souterraines', 'wms', GR),
        ('Risques', 'PPRT_ZONE_RISQIND', 'PPR technologiques', 'wms', GR),
        ('Industrie et pollution', 'INSTALLATIONS_CLASSEES_SIMPLIFIE', 'Installations classées (ICPE)', 'wms', GR),
        ('Industrie et pollution', 'SSP_ETABLISSEMENT', 'Anciens sites industriels (CASIAS)', 'wms', GR),
        ('Industrie et pollution', 'SSP_INSTRUCTION', 'Sites pollués (ex BASOL)', 'wms', GR),
        ('Industrie et pollution', 'SSP_CLASSIFICATION_SIS', "Secteurs d'information sur les sols", 'wms', GR),
        ('Industrie et pollution', 'CANALISATIONS', 'Canalisations de matières dangereuses', 'wms', GR),
        ('Environnement', 'Patrinat_ZNIEFF1', 'ZNIEFF type 1', 'wmts', 'PM_6_16|normal|image/png'),
        ('Environnement', 'Patrinat_ZNIEFF2', 'ZNIEFF type 2', 'wmts', 'PM_6_16|normal|image/png'),
        ('Énergie', 'POTENTIEL.SOLAIRE.BATIMENT', 'Potentiel solaire des toitures', 'wmts', 'PM_6_18|POTENTIEL.SOLAIRE.BATIMENT|image/png'),
        ('Histoire', 'ORTHOIMAGERY.ORTHOPHOTOS.1950-1965', 'Photos aériennes 1950 à 1965', 'wmts', 'PM_0_18|BDORTHOHISTORIQUE|image/png'),
        ('Histoire', 'ORTHOIMAGERY.ORTHOPHOTOS.1980-1995', 'Photos aériennes 1980 à 1995', 'wmts', 'PM_3_18|BDORTHOHISTORIQUE|image/png'),
    ]


def auth_config(user, pwd):
    am = QgsApplication.authManager()
    for cid, cfg in am.availableAuthMethodConfigs().items():
        if cfg.name() == AUTH_NOM:
            am.removeAuthenticationConfig(cid)
    cfg = QgsAuthMethodConfig()
    cfg.setName(AUTH_NOM)
    cfg.setMethod('Basic')
    cfg.setConfig('username', user)
    cfg.setConfig('password', pwd)
    am.storeAuthenticationConfig(cfg)
    return cfg.id()


def uri_pg(hote, authcfg, table, geom, cle, wkb, filtre=''):
    u = QgsDataSourceUri()
    u.setConnection(hote, '5432', 'postgres', '', '', QgsDataSourceUri.SslRequire, authcfg)
    u.setDataSource('public', table, geom, filtre, cle)
    u.setSrid('4326')
    u.setWkbType(wkb)
    return u.uri(False)


def connexion(pwd):
    for hote, user in HOTES:
        cid = auth_config(user, pwd)
        lyr = QgsVectorLayer(uri_pg(hote, cid, 'carto_zonage', 'geom', 'id', QgsWkbTypes.MultiPolygon), 'test', 'postgres')
        if lyr.isValid():
            return hote, cid
    return None, None


def ign(couche, fmt, nom, visible=True, tms='PM', style='normal'):
    url = ('https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=' + couche +
           '&STYLE=' + quote(style) + '&TILEMATRIXSET=' + tms + '&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=' + fmt)
    lyr = QgsRasterLayer('type=xyz&zmin=0&zmax=19&url=' + quote(url, safe=''), nom, 'wms')
    return lyr


def categories(lyr, champ, valeurs, geom='poly'):
    cats = []
    for val, couleur, libelle, opa in valeurs:
        if geom == 'poly':
            s = QgsFillSymbol.createSimple({'color': couleur, 'outline_color': '#3a3a3a', 'outline_width': '0.15'})
        else:
            s = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': couleur, 'outline_color': '#ffffff', 'size': '2.2'})
        s.setOpacity(opa)
        cats.append(QgsRendererCategory(val, s, libelle))
    lyr.setRenderer(QgsCategorizedSymbolRenderer(champ, cats))


def etiquettes(lyr, champ, taille=8, couleur='#5a4510', echelle_max=None):
    p = QgsPalLayerSettings()
    p.fieldName = champ
    f = QgsTextFormat()
    f.setFont(QFont('Arial'))
    f.setSize(taille)
    f.setColor(QColor(couleur))
    b = f.buffer()
    b.setEnabled(True)
    b.setSize(0.8)
    b.setColor(QColor('#ffffff'))
    f.setBuffer(b)
    p.setFormat(f)
    if echelle_max:
        p.scaleVisibility = True
        p.minimumScale = echelle_max
        p.maximumScale = 0
    lyr.setLabeling(QgsVectorLayerSimpleLabeling(p))
    lyr.setLabelsEnabled(True)


def lecture_seule(lyr, editables):
    fc = lyr.editFormConfig()
    for i, f in enumerate(lyr.fields()):
        fc.setReadOnly(i, f.name() not in editables)
    lyr.setEditFormConfig(fc)


def action_url(lyr, nom, url):
    lyr.actions().addAction(QgsAction(QgsAction.OpenUrl, nom, url))


def main():
    pwd, ok = QInputDialog.getText(None, 'IRIS MAP', 'Mot de passe qgis_iris (onglet Outils du dashboard) :', QLineEdit.Password)
    if not ok or not pwd:
        return
    hote, cid = connexion(pwd)
    if not hote:
        QMessageBox.warning(None, 'IRIS MAP', 'Connexion impossible à Supabase. Vérifie le mot de passe et ta connexion.')
        return

    pj = QgsProject.instance()
    pj.clear()
    pj.setCrs(QgsCoordinateReferenceSystem('EPSG:3857'))
    pj.setTitle('IRIS MAP, prospection IRIS REP')
    racine = pj.layerTreeRoot()

    # Fonds IGN
    fonds = racine.addGroup('Fonds IGN')
    for couche, fmt, nom, vis in [
        ('CADASTRALPARCELS.PARCELLAIRE_EXPRESS', 'image/png', 'Cadastre IGN', True),
        ('GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2', 'image/png', 'Plan IGN', True),
        ('ORTHOIMAGERY.ORTHOPHOTOS', 'image/jpeg', 'Photo aérienne IGN', False),
    ]:
        r = ign(couche, fmt, nom)
        if couche.startswith('CADASTRAL'):
            r.renderer().setOpacity(0.75)
        pj.addMapLayer(r, False)
        n = fonds.addLayer(r)
        n.setItemVisibilityChecked(vis)

    donnees = racine.insertGroup(0, 'IRIS MAP')

    # Bâtiments, colorés par priorité, suivi de prospection éditable
    bat = QgsVectorLayer(uri_pg(hote, cid, 'v_qgis_batiments', 'geom', 'batiment_groupe_id', QgsWkbTypes.MultiPolygon), 'Bâtiments par priorité', 'postgres')
    categories(bat, 'priorite', [
        (1, '#b3261e', 'P1 industriel en zone d\'activité', 0.85),
        (2, '#e07a2f', 'P2 industriel hors ZA ou cible en ZA', 0.8),
        (3, '#d9b44a', 'P3 autre cible', 0.75),
        (None, '#9aa0ad', 'Autre bâtiment', 0.25),
    ])
    lecture_seule(bat, ['statut_prospection', 'notes', 'date_dernier_contact', 'prochaine_action'])
    i = bat.fields().indexOf('statut_prospection')
    bat.setEditorWidgetSetup(i, QgsEditorWidgetSetup('ValueMap', {'map': [{s: s} for s in STATUTS]}))
    i = bat.fields().indexOf('date_dernier_contact')
    bat.setEditorWidgetSetup(i, QgsEditorWidgetSetup('DateTime', {'calendar_popup': True, 'display_format': 'dd/MM/yyyy', 'field_format': 'yyyy-MM-dd'}))
    i = bat.fields().indexOf('notes')
    bat.setEditorWidgetSetup(i, QgsEditorWidgetSetup('TextEdit', {'IsMultiline': True}))
    bat.setMapTipTemplate(
        '<b>[% CASE WHEN "priorite" IS NOT NULL THEN \'P\' || "priorite" || \' · \' || "priorite_motif" ELSE \'Hors cible\' END %]</b><br>'
        '[% "usage" %] · emprise [% format_number("surface_emprise",0) %] m² · plancher estimé [% format_number("surface_plancher_estimee",0) %] m²<br>'
        'Propriétaire : [% coalesce("proprietaires", \'personne physique ou inconnu\') %]<br>'
        '[% "adresse" %]<br>'
        '[% CASE WHEN "statut_prospection" IS NOT NULL THEN \'Suivi : \' || "statut_prospection" END %]')
    action_url(bat, 'Propriétaire sur Pappers', 'https://www.pappers.fr/entreprise/[% regexp_substr("siren_proprietaires", \'[0-9]{9}\') %]')
    action_url(bat, 'Propriétaire sur Annuaire Entreprises', 'https://annuaire-entreprises.data.gouv.fr/entreprise/[% regexp_substr("siren_proprietaires", \'[0-9]{9}\') %]')
    action_url(bat, 'Fiche complète IRIS MAP', 'https://dashboard-iris-h.pages.dev/carto.html#[% "batiment_groupe_id" %]')
    action_url(bat, 'Street View', 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=[% y(transform(centroid($geometry), @layer_crs, \'EPSG:4326\')) %],[% x(transform(centroid($geometry), @layer_crs, \'EPSG:4326\')) %]')
    pj.addMapLayer(bat, False)
    donnees.addLayer(bat)

    # Entreprises SIRENE
    etab = QgsVectorLayer(uri_pg(hote, cid, 'v_qgis_etablissements', 'geom', 'siret', QgsWkbTypes.Point), 'Entreprises SIRENE', 'postgres')
    categories(etab, 'etat', [('actif', '#2e7d4f', 'Actif', 0.9), ('fermé', '#a33a3a', 'Fermé', 0.7)], geom='point')
    etab.setMapTipTemplate('<b>[% "nom" %]</b><br>NAF [% "naf" %] · effectif [% "tranche_effectif" %] · [% "etat" %]<br>Dirigeants : [% "dirigeants" %]')
    action_url(etab, 'Entreprise sur Pappers', 'https://www.pappers.fr/entreprise/[% "siren" %]')
    action_url(etab, 'Établissement sur Annuaire Entreprises', 'https://annuaire-entreprises.data.gouv.fr/etablissement/[% "siret" %]')
    pj.addMapLayer(etab, False)
    donnees.addLayer(etab).setItemVisibilityChecked(False)

    # Ventes DVF
    dvf = QgsVectorLayer(uri_pg(hote, cid, 'v_qgis_ventes', 'geom', 'id', QgsWkbTypes.Point), 'Ventes DVF depuis 2021', 'postgres')
    categories(dvf, 'type_local', [
        ('Local industriel. commercial ou assimilé', '#6a3d9a', 'Local activité ou commerce', 0.9),
        ('Terrain', '#33a02c', 'Terrain', 0.8),
        ('Maison', '#bbbbbb', 'Maison', 0.5),
        ('Appartement', '#bbbbbb', 'Appartement', 0.5),
        ('Dépendance', '#dddddd', 'Dépendance', 0.4),
    ], geom='point')
    dvf.setMapTipTemplate('<b>[% format_number("valeur_fonciere",0) %] €</b> le [% format_date("date_mutation",\'dd/MM/yyyy\') %]<br>[% "type_local" %] · bâti [% "surface_reelle_bati" %] m² · terrain [% "surface_terrain" %] m²<br>[% CASE WHEN "prix_m2_bati" IS NOT NULL THEN format_number("prix_m2_bati",0) || \' €/m² bâti\' END %]')
    pj.addMapLayer(dvf, False)
    donnees.addLayer(dvf).setItemVisibilityChecked(False)

    # Zonage PLU
    zon = QgsVectorLayer(uri_pg(hote, cid, 'carto_zonage', 'geom', 'id', QgsWkbTypes.MultiPolygon), 'Zonage PLU', 'postgres')
    categories(zon, 'activite', [(True, '#c2551f', 'Zone d\'activité', 0.25), (False, '#f2e2a0', 'Autre zone', 0.12)])
    etiquettes(zon, 'libelle', 9)
    zon.setMapTipTemplate('<b>[% "libelle" %]</b><br>[% "libelong" %]')
    pj.addMapLayer(zon, False)
    donnees.addLayer(zon).setItemVisibilityChecked(False)

    # Repérages, dessinables et partagés avec la page web
    for nom_couche, wkb, filtre, couleur in [
        ('Repérages zones', QgsWkbTypes.MultiPolygon, "GeometryType(geom) IN ('POLYGON','MULTIPOLYGON')", '#7b2cbf'),
        ('Repérages points', QgsWkbTypes.Point, "GeometryType(geom) = 'POINT'", '#7b2cbf'),
    ]:
        rep = QgsVectorLayer(uri_pg(hote, cid, 'carto_reperages', 'geom', 'id', wkb, filtre), nom_couche, 'postgres')
        if wkb == QgsWkbTypes.Point:
            rep.renderer().setSymbol(QgsMarkerSymbol.createSimple({'name': 'star', 'color': couleur, 'outline_color': '#ffffff', 'size': '4'}))
        else:
            sym = QgsFillSymbol.createSimple({'color': '123,44,191,60', 'outline_color': couleur, 'outline_width': '0.6', 'outline_style': 'dash'})
            rep.renderer().setSymbol(sym)
        etiquettes(rep, 'nom', 9, couleur)
        lecture_seule(rep, ['nom', 'type_reperage', 'statut', 'contact', 'notes', 'date_reperage', 'auteur'])
        rep.setEditorWidgetSetup(rep.fields().indexOf('type_reperage'), QgsEditorWidgetSetup('ValueMap', {'map': [{s: s} for s in TYPES_REP]}))
        rep.setEditorWidgetSetup(rep.fields().indexOf('statut'), QgsEditorWidgetSetup('ValueMap', {'map': [{s: s} for s in STATUTS_REP]}))
        rep.setEditorWidgetSetup(rep.fields().indexOf('notes'), QgsEditorWidgetSetup('TextEdit', {'IsMultiline': True}))
        rep.setEditorWidgetSetup(rep.fields().indexOf('date_reperage'), QgsEditorWidgetSetup('DateTime', {'calendar_popup': True, 'display_format': 'dd/MM/yyyy', 'field_format': 'yyyy-MM-dd'}))
        rep.setMapTipTemplate('<b>[% "nom" %]</b> · [% "type_reperage" %]<br>[% "statut" %][% CASE WHEN "surface_m2" IS NOT NULL THEN \' · \' || format_number("surface_m2",0) || \' m²\' END %]<br>[% "notes" %]')
        pj.addMapLayer(rep, False)
        donnees.insertLayer(0, rep)

    # Parcelles vectorielles, pour sélectionner et mesurer
    par = QgsVectorLayer(uri_pg(hote, cid, 'carto_parcelles', 'geom', 'idu', QgsWkbTypes.MultiPolygon), 'Parcelles (sélection)', 'postgres')
    sym = QgsFillSymbol.createSimple({'color': '0,0,0,0', 'outline_color': '#2f5d8a', 'outline_width': '0.2'})
    par.renderer().setSymbol(sym)
    etiquettes(par, 'numero', 7, '#2f5d8a', echelle_max=3000)
    par.setMapTipTemplate('Parcelle <b>[% "idu" %]</b> · [% format_number("contenance",0) %] m²')
    pj.addMapLayer(par, False)
    donnees.addLayer(par).setItemVisibilityChecked(False)

    # Données publiques : flux officiels affichés sans import, décochés par défaut
    GR = 'https://mapsref.brgm.fr/wxs/georisques/risques'
    GPF = 'https://data.geopf.fr/wms-v/ows'
    publiques = racine.insertGroup(1, 'Données publiques')
    for groupe, couche, nom, typ, src in PUBLIQUES(GR, GPF):
        g = publiques.findGroup(groupe) or publiques.addGroup(groupe)
        if typ == 'wms':
            r = QgsRasterLayer('crs=EPSG:3857&format=image/png&layers=' + couche + '&styles=&url=' + src, nom, 'wms')
        else:
            tms, style, fmt = src.split('|')
            r = ign(couche, fmt, nom, tms=tms, style=style)
        pj.addMapLayer(r, False)
        g.addLayer(r).setItemVisibilityChecked(False)
    publiques.setExpanded(False)

    # Vue initiale sur l'emprise des bâtiments
    tr = QgsCoordinateTransform(bat.crs(), pj.crs(), pj)
    iface.mapCanvas().setExtent(tr.transformBoundingBox(bat.extent()))
    try:
        iface.actionMapTips().setChecked(True)
    except Exception:
        pass
    iface.setActiveLayer(bat)
    iface.mapCanvas().refresh()

    os.makedirs(os.path.dirname(PROJET), exist_ok=True)
    pj.write(PROJET)
    QMessageBox.information(None, 'IRIS MAP', 'Projet créé et enregistré :\n' + PROJET +
                            '\n\nSurvol : infobulle. Clic avec l\'outil Identifier : fiche et suivi.\n'
                            'Modifier le suivi : sélectionner la couche Bâtiments, crayon d\'édition, puis enregistrer.')


main()
