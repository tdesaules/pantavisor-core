# CI, provenance et publication

Ce document décrit le parcours initial, conservé jusqu'à activation du catalogue.
Le nouveau workflow hébergé et son ordre de publication sont décrits dans
[la migration CI](ci-migration.md).

`check.yml` exécute les tests et la syntaxe à chaque push/PR. `release.yml` est
manuel, sur runner `[self-hosted, linux, x64, pantavisor]` avec Python ≥3.11, Git,
Podman rootless, unsquashfs et qemu-aarch64. Prévoir 16 Gio RAM et 150 Gio libres.
Le checkout est neuf par exécution ; aucun cache Yocto externe n'est réutilisé.

`build/provenance.py` capture l'identité des sources avant le build et les
empreintes des sorties après succès. `build/package.py` refuse toute modification
des sources ou des sorties depuis le build. `build-provenance.json` contient aussi
la durée. Reconstruire les anciennes sorties avant de les empaqueter.

Pour publier, lancer le workflow depuis `v<VERSION>` avec `publish=true` :

- image OCI : `ghcr.io/<owner>/pantavisor-core:<VERSION>` ;
- composant ORAS : `ghcr.io/<owner>/pantavisor-core/component:<VERSION>`.

Le workflow exige un build propre, les tests, le smoke ARM64 et le build OCI.
Il affiche le digest de l'artefact ORAS que System doit consommer. La qualification
fonctionnelle base/k0s reste dans System. La présence du workflow ne constitue
pas une preuve de publication ou de build froid réussi ; conserver les rapports
du premier lancement. Nettoyer les anciens checkouts du runner après archivage.
