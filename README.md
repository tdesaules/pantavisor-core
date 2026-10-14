# Pantavisor Core

Composant de gestion ARM64 pour un hôte Pantavisor : Bash, DHCP, SSH par clé,
synchronisation NTP, client `pvcontrol` et outils d'administration Kubernetes
**kubectl, k0sctl et k9s inclus systématiquement**. Version propre au projet : **0.1.0**.

Une seule image et un seul composant sont produits : **`core`**. Les clients
Kubernetes sont disponibles pour l'administration, même si aucun serveur k0s
n'est déployé. Le serveur reste un composant indépendant.

Ce dépôt se construit sans checkout System ou k0s. Les dépendances publiques
Yocto sont épinglées dans `kas/`. L'architecture initiale est ARMv8-A/musl ;
l'absence de couplage à une carte ne constitue pas une qualification de toutes
les plateformes ARM64.

## Structure

- `services/` : code du Core, indépendant des recettes de build.
- `config/` : exemples de configuration injectée au déploiement.
- `runtime/` : contrat versionné et template LXC consommés par System.
- `build/meta-core/` : recettes Yocto, Bash épinglé et clients Kubernetes.
- `build/build.sh` : lancement local de KAS dans Podman rootless.
- `build/package.py` : export d'un composant public vérifiable.
- `build/Containerfile` : image OCI à partir du rootfs Yocto, sans compilateurs.
- `build/smoke.py` : vérification des binaires ARM64 avec QEMU utilisateur.
- `tests/` : contrats de packaging et syntaxe des services.
- `VERSION` : version de Core, distincte de la version System.

## Construction locale

Prérequis : Linux, Git, Python ≥3.11, [Task](https://taskfile.dev/) v3 et Podman rootless.
`task --list` affiche les tâches disponibles. Sans argument, `task` lance `build`.

```sh
task check
task build
task package
task oci
```

L'export est `dist/core/` et l'image locale est `localhost/pantavisor-core:0.1.0`.
Le tag suit `VERSION`, également inscrite dans le label OCI et le descripteur.
Aucune publication automatique n'est faite.

Les répertoires d'export doivent être nouveaux. Déplacer un ancien export avant
de relancer le packaging, ou choisir `build/package.py --output <chemin>`.

Des caches publics existants peuvent être fournis explicitement :

```sh
DOWNLOAD_CACHE=/chemin/downloads SSTATE_CACHE=/chemin/sstate-cache task build
```

Ils sont facultatifs ; le premier build sans cache télécharge ses dépendances.
La recette amont de Pantavisor est encore compilée pour fournir `pvcontrol` :
cela ne construit pas le BSP ni l'image System et ne dépend pas du dépôt System.

## Artefacts et exécution

L'export contient `component.json`, les rootfs SquashFS et tar, le manifeste des
paquets, le SBOM et le contrat runtime. System peut en recevoir une copie et
l'assembler sans accéder à ce dépôt. Les versions des autres composants peuvent
être différentes.

`task oci` construit une véritable image OCI ARM64. Son utilisateur est root
parce que DHCP et NTP administrent le réseau et l'horloge partagés. Le contrat
LXC et les capacités requises restent nécessaires : ce n'est pas un service
applicatif ordinaire que l'on démarre arbitrairement sur l'hôte.

Voir [le contrat d'exécution](docs/runtime-contract.md). Pour le smoke test,
installer `unsquashfs` et `qemu-aarch64`, puis :

```sh
python3 build/smoke.py dist/core
```

## État de l'extraction

Projet neuf, versions réinitialisées ; aucune reprise d'historique Git.
Le packaging exige les trois clients Kubernetes et leurs métadonnées de version.
Les tests ARM64 exécutent Bash, kubectl, k0sctl et k9s sans condition de profil.
Core est consommé par System dans les compositions base et k0s.
La CI et la publication seront configurées séparément. Aucun accès carte n'est
nécessaire pour les commandes ci-dessus.
