# CLAUDE.md, dépôt dashboard-iris-h-v2

## Écriture des fichiers Drive

Consigne permanente posée par Yannis le 23 octobre 2026. Elle remplace toute règle antérieure sur create_file, sur le dépôt manuel des gros fichiers et sur la création d'un nouveau fichier à chaque version.

### Environnement

Une session locale tourne sur le poste de Yannis. Elle voit G:\Mon Drive, synchronisé par Google Drive pour ordinateur, et elle gère le dashboard, Supabase, les déploiements et l'écriture des fichiers Drive.

Une session cloud, Claude Code web ou conteneur Anthropic, ne voit pas G: et n'a aucun accès OAuth à Google. Dans une session de ce type, les fichiers de moins de 30 000 octets passent par le connecteur Drive, et les plus gros sont renvoyés à une session locale, accompagnés d'un prompt prêt à coller.

### Contexte

Le connecteur Google Drive a trois limites. create_file exige tout le contenu dans un seul appel, et un appel de plus de 30 000 octets environ risque d'être coupé et d'échouer. update_file ne modifie que les métadonnées, jamais le contenu. Chaque nouvelle version crée donc un nouveau fichier, un nouveau lien, et oblige à mettre à jour la fiche documents_claude.

### Méthode en session locale

1. Tout fichier destiné à Drive est écrit directement dans G:\Mon Drive\..., qui se synchronise automatiquement.
2. Pour modifier un fichier existant, l'éditer sur place, par morceaux si besoin. Le fichier garde son identifiant Drive, donc son lien ne change pas et la fiche documents_claude n'a pas à être modifiée, sauf la date et le numéro de version.
3. La taille n'est plus une contrainte. Aucun fichier n'est renvoyé à Yannis pour un dépôt manuel au motif qu'il est trop lourd.
4. Le connecteur Google Drive sert uniquement à lire un fichier, à retrouver un identifiant ou un lien, et à créer un Google Doc, Sheet ou Slides natif.

### Versionnage

Avant toute réécriture importante, copier la version courante dans le sous dossier old du même dossier, suffixée de sa date au format AAAAMMJJ, puis réécrire le fichier courant au même chemin. Ne jamais rien supprimer. Drive conserve en plus l'historique des révisions.

### Contrôle après écriture

1. Relire la taille et la fin du fichier écrit pour confirmer qu'il est complet.
2. Attendre la synchronisation, puis vérifier avec le connecteur que le fichier Drive porte bien la nouvelle date de modification.
3. Donner à Yannis le chemin G: complet et le lien Drive du fichier.

### Blocage

Si G:\Mon Drive n'est pas accessible, le dire en une ligne et attendre les instructions de Yannis. Ne pas repasser par create_file pour contourner le problème.

## Règle de modification du dashboard

Une seule session est habilitée à modifier le dashboard IRIS H, la session Claude Code dashboard, dépôt dashboard-iris-h-v2. Aucune autre session ne dépose dans le bucket dashboard-site ni ne déclenche site-deploy. Avant tout site-put, comparer octet par octet la page en ligne avec la base de travail, et vérifier la page déployée après le site-deploy.
