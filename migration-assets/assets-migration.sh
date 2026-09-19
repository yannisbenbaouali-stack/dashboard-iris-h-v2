#!/usr/bin/env bash
# Migration des visuels Supabase vers assets.irisrep.com
# Usage : ./assets-migration.sh <etape>
# Etapes : ping | inventaire | export | depot | verif | mapping | restes
#
# Aucun credential dans ce fichier. Tout vient de .env, non versionne.
# Voir README.md pour l'ordre d'execution.

set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAVAIL="$ICI/_travail"
SRC="$TRAVAIL/src"
OUT="$TRAVAIL/out"
MANIFEST="$TRAVAIL/manifest.tsv"
MAPPING="$TRAVAIL/mapping.csv"
JOURNAL="$TRAVAIL/journal.log"

[ -f "$ICI/.env" ] || { echo "manque $ICI/.env, copier .env.example"; exit 1; }
# shellcheck disable=SC1091
source "$ICI/.env"

: "${SUPABASE_REF:?}"
: "${SUPABASE_SECRET:?}"
: "${DEPOT_URL:?}"
: "${DEPOT_TOKEN:?}"
DEPOT_CHAMP_FICHIER="${DEPOT_CHAMP_FICHIER:-file}"
DEPOT_CHAMP_CHEMIN="${DEPOT_CHAMP_CHEMIN:-path}"
BASE_PUBLIQUE="${BASE_PUBLIQUE:-https://assets.irisrep.com}"

API="https://$SUPABASE_REF.supabase.co/storage/v1"
BUCKETS=(logos visuels dashboard-assets)

mkdir -p "$TRAVAIL" "$SRC" "$OUT"

log() { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$JOURNAL"; }
besoin() { command -v "$1" >/dev/null || { echo "outil manquant : $1"; exit 1; }; }

besoin curl
besoin jq

# ---------------------------------------------------------------- nommage
# minuscules, sans accents, espaces et underscores en tirets, extension gardee
normalise() {
  printf '%s' "$1" \
    | iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null || printf '%s' "$1"
}

cible_pour() {
  local bucket="$1" chemin="$2" cible=""
  case "$bucket/$chemin" in
    */_archives_originaux/*) return 1 ;;          # sources HD, restent sur Drive
    *.DS_Store|*/_test.*)    return 1 ;;
  esac
  case "$bucket" in
    logos)
      case "$chemin" in
        sig/*)   cible="sig/${chemin#sig/}" ;;
        *)       cible="logos/$chemin" ;;
      esac ;;
    visuels)
      cible="${chemin#arristo/}"
      cible="arristo/$cible" ;;
    dashboard-assets)
      case "$chemin" in
        logos/*)       cible="dashboard/$chemin" ;;
        events/*)      cible="arristo/$chemin" ;;
        electricien/*) cible="$chemin" ;;
        dossiers/*)    cible="docs/${chemin#dossiers/}" ;;
        iris_rep/*)    cible="docs/${chemin#iris_rep/}" ;;
        *)             cible="dashboard/$chemin" ;;
      esac ;;
  esac
  # minuscules, sans accents, underscores et espaces en tirets, slash conserve
  normalise "$cible" | tr '[:upper:]' '[:lower:]' | tr '_ ' '--' | tr -s '-'
}

# ---------------------------------------------------------------- etapes
etape_ping() {
  log "ping $DEPOT_URL"
  curl -sS -m 20 -H "X-Depot-Token: $DEPOT_TOKEN" "$DEPOT_URL?action=ping" | tee -a "$JOURNAL"; echo
  log "list racine"
  curl -sS -m 30 -H "X-Depot-Token: $DEPOT_TOKEN" "$DEPOT_URL?action=list&path=." | tee -a "$JOURNAL"; echo
  echo
  echo "Si la reponse upload attend d'autres noms de champs que '$DEPOT_CHAMP_FICHIER' et"
  echo "'$DEPOT_CHAMP_CHEMIN', ajuster DEPOT_CHAMP_FICHIER et DEPOT_CHAMP_CHEMIN dans .env."
}

lister_bucket() { # bucket prefixe -> lignes "chemin<TAB>taille"
  local bucket="$1" prefixe="${2:-}" offset=0 lot
  while :; do
    lot="$(curl -sS -m 60 -X POST "$API/object/list/$bucket" \
      -H "apikey: $SUPABASE_SECRET" -H "Authorization: Bearer $SUPABASE_SECRET" \
      -H "Content-Type: application/json" \
      -d "$(jq -nc --arg p "$prefixe" --argjson o "$offset" \
          '{prefix:$p,limit:100,offset:$o,sortBy:{column:"name",order:"asc"}}')")"
    [ "$(jq 'length' <<<"$lot")" -gt 0 ] || break
    while IFS=$'\t' read -r nom taille id; do
      if [ "$id" = "null" ]; then
        lister_bucket "$bucket" "${prefixe:+$prefixe/}$nom"
      else
        printf '%s\t%s\n' "${prefixe:+$prefixe/}$nom" "$taille"
      fi
    done < <(jq -r '.[] | [.name, (.metadata.size // 0), (.id // "null")] | @tsv' <<<"$lot")
    offset=$((offset + 100))
  done
}

etape_inventaire() {
  : > "$MANIFEST"
  local total=0 retenu=0 ecarte=0
  for bucket in "${BUCKETS[@]}"; do
    log "inventaire $bucket"
    while IFS=$'\t' read -r chemin taille; do
      total=$((total + 1))
      if cible="$(cible_pour "$bucket" "$chemin")"; then
        printf '%s\t%s\t%s\t%s\n' "$bucket" "$chemin" "$cible" "$taille" >> "$MANIFEST"
        retenu=$((retenu + 1))
      else
        ecarte=$((ecarte + 1))
      fi
    done < <(lister_bucket "$bucket")
  done
  local poids
  poids="$(awk -F'\t' '{s+=$4} END{printf "%.1f", s/1048576}' "$MANIFEST")"
  log "manifest : $retenu fichiers retenus, $ecarte ecartes, $total vus, $poids Mo a telecharger"
  echo
  echo "Relire $MANIFEST avant l'etape export."
  echo "Colonnes : bucket, chemin source, chemin cible, taille."
  echo "Doublons de cible eventuels :"
  cut -f3 "$MANIFEST" | sort | uniq -d || true
}

etape_export() {
  [ -s "$MANIFEST" ] || { echo "lancer d'abord : $0 inventaire"; exit 1; }
  local poids
  poids="$(awk -F'\t' '{s+=$4} END{printf "%.0f", s/1048576}' "$MANIFEST")"
  log "telechargement de $poids Mo depuis Supabase, egress ponctuel"
  while IFS=$'\t' read -r bucket chemin cible _; do
    mkdir -p "$SRC/$bucket/$(dirname "$chemin")" "$OUT/$(dirname "$cible")"
    if [ ! -f "$SRC/$bucket/$chemin" ]; then
      curl -sS -m 120 -o "$SRC/$bucket/$chemin" \
        "$API/object/public/$bucket/$chemin" || { log "ECHEC telechargement $bucket/$chemin"; continue; }
    fi
    case "$cible" in
      sig/*)
        if command -v magick >/dev/null || command -v convert >/dev/null; then
          local im; im="$(command -v magick || command -v convert)"
          "$im" "$SRC/$bucket/$chemin" -resize 200x -strip "PNG32:$OUT/$cible"
          command -v pngquant >/dev/null && pngquant --force --skip-if-larger --quality 60-90 \
            --output "$OUT/$cible" "$OUT/$cible" || true
          local ko; ko=$(( $(stat -c%s "$OUT/$cible" 2>/dev/null || stat -f%z "$OUT/$cible") / 1024 ))
          [ "$ko" -ge 50 ] && log "ALERTE $cible fait $ko Ko, limite 50 Ko"
        else
          log "ImageMagick absent, signature $cible copiee sans redimensionnement"
          cp "$SRC/$bucket/$chemin" "$OUT/$cible"
        fi ;;
      *.gif)
        log "ALERTE gif anime $cible, a convertir ou ecarter, non copie" ;;
      *)
        cp "$SRC/$bucket/$chemin" "$OUT/$cible" ;;
    esac
  done < "$MANIFEST"
  cat > "$OUT/.htaccess" <<'HT'
Options -Indexes
AddType image/webp .webp
AddType image/svg+xml .svg
<IfModule mod_headers.c>
  <FilesMatch "\.(png|jpe?g|gif|webp|svg|ico|pdf)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
    Header set Access-Control-Allow-Origin "*"
  </FilesMatch>
</IfModule>
HT
  log "export termine dans $OUT"
  du -sh "$OUT"
}

etape_depot() {
  [ -d "$OUT" ] || { echo "lancer d'abord : $0 export"; exit 1; }
  local n=0
  while IFS= read -r fichier; do
    local cible="${fichier#"$OUT"/}"
    local reponse
    reponse="$(curl -sS -m 180 -X POST "$DEPOT_URL" \
      -H "X-Depot-Token: $DEPOT_TOKEN" \
      -F "action=upload" \
      -F "$DEPOT_CHAMP_CHEMIN=$cible" \
      -F "$DEPOT_CHAMP_FICHIER=@$fichier")" || reponse="ECHEC reseau"
    case "$reponse" in
      *rror*|*ECHEC*|*denied*) log "ECHEC $cible : $reponse" ;;
      *) n=$((n + 1)); log "depose $cible" ;;
    esac
  done < <(find "$OUT" -type f | sort)
  log "$n fichiers deposes"
}

etape_verif() {
  [ -s "$MANIFEST" ] || { echo "lancer d'abord : $0 inventaire"; exit 1; }
  local ko=0 ok=0
  while IFS=$'\t' read -r _ _ cible _; do
    local code
    code="$(curl -sS -m 30 -o /dev/null -w '%{http_code}' -I "$BASE_PUBLIQUE/$cible")"
    if [ "$code" = "200" ]; then ok=$((ok + 1)); else ko=$((ko + 1)); log "HTTP $code $BASE_PUBLIQUE/$cible"; fi
  done < "$MANIFEST"
  log "verif : $ok en 200, $ko en erreur"
  [ "$ko" -eq 0 ] || exit 1
}

etape_mapping() {
  [ -s "$MANIFEST" ] || { echo "lancer d'abord : $0 inventaire"; exit 1; }
  { echo "ancienne_url,nouvelle_url"
    while IFS=$'\t' read -r bucket chemin cible _; do
      echo "$API/object/public/$bucket/$chemin,$BASE_PUBLIQUE/$cible"
    done < "$MANIFEST"
  } > "$MAPPING"
  log "mapping ecrit dans $MAPPING"
  echo "A utiliser pour les signatures Gmail, les pages du bucket dashboard-site,"
  echo "les projets Lovable et les supports ARRISTO."
}

etape_restes() {
  cat <<'SQL'
Controle des appels restants, a passer dans le SQL editor Supabase
ou via le MCP Supabase, fenetre maximale 24 heures :

  select log_attributes['request.path'] as chemin,
         count(*) as hits
  from logs
  where source = 'edge_logs'
    and log_attributes['request.path'] like '/storage/v1/object/public/%'
  group by chemin
  order by hits desc;

Tant que cette requete renvoie des lignes sur logos, visuels ou dashboard-assets,
ne pas basculer les buckets en prive. Verifier deux jours de suite.
SQL
}

case "${1:-}" in
  ping)       etape_ping ;;
  inventaire) etape_inventaire ;;
  export)     etape_export ;;
  depot)      etape_depot ;;
  verif)      etape_verif ;;
  mapping)    etape_mapping ;;
  restes)     etape_restes ;;
  *) sed -n '1,8p' "$0"; exit 1 ;;
esac
