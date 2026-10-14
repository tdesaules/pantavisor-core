SUMMARY = "Core DHCP, SSH and local Pantavisor administration"
LICENSE = "MIT"
FILESEXTRAPATHS:prepend := "${CORE_REPO_ROOT}/services:"
require conf/component.inc
PV = "${CORE_VERSION}"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"
SRC_URI = "file://network file://udhcpc.script file://core-init file://time-sync"
S = "${WORKDIR}"
RDEPENDS:${PN} = "busybox dropbear-pv pantavisor-pvcontrol lxc6-pv"

do_install() {
    install -d ${D}${libdir}/pantavisor-core ${D}${sysconfdir}/dropbear ${D}${sysconfdir}/pantavisor \
        ${D}/home/root/.ssh ${D}/data ${D}/pantavisor \
        ${D}/proc ${D}/sys ${D}/dev/pts ${D}/run ${D}/tmp
    install -d ${D}${libexecdir}/pantavisor
    install -m 0755 ${WORKDIR}/network ${WORKDIR}/core-init ${WORKDIR}/time-sync ${D}${libexecdir}/pantavisor/
    install -m 0755 ${WORKDIR}/udhcpc.script ${D}${libdir}/pantavisor-core/
    printf '/bin/sh\n/bin/bash\n/usr/bin/bash\n' > ${D}${sysconfdir}/shells
    chmod 0700 ${D}/home/root ${D}/home/root/.ssh
    chmod 1777 ${D}/tmp
}
FILES:${PN} += "${libdir}/pantavisor-core /home/root /data /pantavisor /proc /sys /dev /run /tmp"

do_install[postfuncs] += "write_core_release"
python write_core_release() {
    import hashlib
    import json
    from pathlib import Path
    source = Path(d.getVar('WORKDIR'))
    names = ('network', 'udhcpc.script', 'core-init', 'time-sync')
    hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in names}
    release = {
        'name': 'pantavisor-core', 'version': d.getVar('PV'),
        'build_system': 'yocto', 'service_sources': hashes,
        'shells': {'bash': '5.3.20'},
        'admin_interface': 'native',
        'service_sources_sha256': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
    }
    release['kubernetes_tools'] = {'kubectl': '1.36.4', 'k0sctl': '0.33.1', 'k9s': '0.51.0'}
    (Path(d.getVar('D')) / 'etc/pantavisor/core-release.json').write_text(json.dumps(release, sort_keys=True, indent=2) + '\n')
}
