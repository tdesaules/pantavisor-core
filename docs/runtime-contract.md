# Contrat `pantavisor-core-v1`

Le descripteur machine est [`runtime/contract.json`](../runtime/contract.json) ;
le template LXC est [`runtime/lxc.conf.in`](../runtime/lxc.conf.in).

## Entrées du déploiement

- `/etc/pantavisor/network.conf` : `NETWORK_INTERFACE`, `SSH_PORT` et éventuellement
  `ETHERNET_MAC`. Sans interface explicite, une unique interface liée à un pilote
  est sélectionnée. Plusieurs candidates sont refusées ; aucun nom de pilote
  Qualcomm ou de carte n'est codé en dur.
- `/etc/pantavisor/time.conf` : `NTP_SERVERS` et éventuellement `TIME_STATUS_DIR`.
- `/home/root/.ssh/authorized_keys` et clé Dropbear dans
  `/etc/dropbear/dropbear_ed25519_host_key` : fournis dans l'état privé, jamais
  intégrés à l'image publique.
- `/data` : volume persistant appartenant à ce Core.
- `/run/platform` : espace de contrôle fourni par l'hôte, dont le marqueur
  atomique `time-ready` après synchronisation initiale.
- `/pantavisor` : API locale et métadonnées exposées au rôle de gestion.

Le template reçoit le budget mémoire, le poids CPU et les sources de montages
depuis System. Il ne choisit aucun disque ni partition physique.

## Cycle de vie

`init.lxc.static` lance `/usr/libexec/pantavisor/core-init`. Core supervise DHCP,
SSH et NTP ; SIGTERM provoque l'arrêt des services. Le signal Pantavisor `READY`
est envoyé après le bail DHCP. Il n'affirme pas que l'horloge est déjà synchronisée :
les consommateurs attendent le marqueur `time-ready` séparément.

Les chemins `/trial-status` et `/boot-state`, s'ils sont fournis par System,
sont des observations du système hôte. Le choix du prochain boot via
`/run/platform/next` appartient au contrat de l'hôte, pas au service Core.

## Outils Kubernetes inclus

Core déclare systématiquement la capacité `kubernetes-clients`. Il contient
kubectl 1.36.4, k0sctl 0.33.1 et k9s 0.51.0. Le kubeconfig est fourni à l'exécution via
`/k0s-access/admin.conf`, monté en lecture seule ; les caches restent dans `/data`.
Core ne contient aucun serveur k0s. Sans kubeconfig fourni, les clients restent
installés ; cela ne bloque pas le démarrage des services Core.

Les images et interfaces de ce nouveau projet doivent être assemblées avec les
contrats correspondants ; les anciens chemins `/usr/libexec/ventuno` et les
anciens fichiers de configuration du monorepo ne constituent pas cette ABI.
