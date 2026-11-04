# Migration vers les Docker Actions

La nouvelle chaîne est implémentée dans le catalogue `tdesaules/github-actions`.
Son activation attend une release publiée contenant toutes les actions : aucun
tag fictif ou digest d'image local ne doit entrer dans le workflow actif.

## Activation après publication du catalogue

Depuis le checkout du catalogue, avec Python, `gh` et ORAS disponibles :

```sh
python3 scripts/pantavisor_consumers.py --project core \
  --catalogue-tag "$CATALOGUE_TAG" --directory ../pantavisor-core
```

`CATALOGUE_TAG` est le vrai tag stable publié, sans préfixe `v`. L'outil vérifie
la release, les interfaces d'actions et leurs images par digest avant toute
édition. Il génère `.github/workflows/main.yml`, archive les anciens workflows
dans `.github/legacy-workflows/` et consigne le tag dans `.github/pantavisor-ci.json`.
Relire le diff puis committer et pousser ce dépôt.

## Développement et release

- Push de branche : sélection des contrôles, lint, build et tests concernés.
- Fusion vers `main` ; les push directs restent possibles. Pas de trigger PR.
- Lancement manuel sur `main` : calcul Conventional Commits, VERSION/changelog,
  commit candidat exporté dans un Git bundle, construction de ce commit exact.
- Build KAS sur `ubuntu-24.04`, avec deux tâches via `kas/ci.yml`. Les sorties
  sont préservées avant suppression de l'arbre de build.
- Qualification ARM64, SBOM et Grype au seuil `high` ; aucun rebuild dans `test`.
- Après qualification, l'App pousse atomiquement le commit sur `main` et son tag
  annoté `v<VERSION>`. Un `main` avancé ou un tag existant est refusé.
- Le tag déclenche la publication des mêmes archives/composants par digest,
  signature et vérification Cosign, puis la GitHub Release avec leurs références.

Les images publiques n'utilisent pas de tag mutable de version dans ce parcours.
La GitHub Release fournit la correspondance version/digests. Les reçus et archives
de qualification sont conservés 30 jours ; une reprise sans ces preuves échoue
explicitement, sans reconstruire ni remplacer la version publiée.

## Configuration GitHub

Configurer `RELEASE_APP_ID` comme variable et `RELEASE_APP_PRIVATE_KEY` comme
secret, avec l'App installée sur ce dépôt et les droits de push nécessaires.
L'accès est vérifié dès la préparation, avant le build long. Le token App permet
au push du tag de déclencher un nouveau workflow.

Configurer séparément `RENOVATE_TOKEN` pour le bot de maintenance et désactiver
l'App Renovate hébergée si elle pilote déjà ce dépôt. `renovate.json` couvre les
actions et Containerfiles ; les commits KAS et les versions/checksums couplés des
recettes Yocto nécessitent une mise à jour coordonnée et une qualification.

## À surveiller

Les six jobs sont `check`, `lint`, `build`, `test`, `release`, `maintenance`.
Surveiller l'espace/durée dans `build-diagnostics-core`, les tests de binaires,
les rapports Syft/Grype, la correspondance source/reçu et les deux signatures.
La maintenance rescane les images publiées sans les reconstruire. Les alertes
`high` bloquent ; elles ne sont pas ignorées pour faciliter une publication.

Les contrôles de services et d'intégration complète restent qualifiés par System.
Les clés, disques et états privés ne font pas partie des artefacts de release.
