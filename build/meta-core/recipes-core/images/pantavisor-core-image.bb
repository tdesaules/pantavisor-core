SUMMARY = "Core connectivity and administration container for Pantavisor"
LICENSE = "MIT"
require conf/component.inc
PV = "${CORE_VERSION}"
inherit image

PACKAGE_INSTALL = "busybox base-passwd curl dropbear-pv pantavisor-pvcontrol lxc6-pv core-service core-bash core-kubernetes-tools ${ROOTFS_BOOTSTRAP_INSTALL}"
IMAGE_FEATURES = ""
IMAGE_LINGUAS = ""
IMAGE_FSTYPES = "squashfs tar.gz"
IMAGE_NAME_SUFFIX = ""
IMAGE_ROOTFS_SIZE = "8192"
IMAGE_ROOTFS_EXTRA_SPACE = "0"
EXTRA_IMAGEDEPENDS = ""
KERNEL_DEPLOY_DEPEND = ""
NO_RECOMMENDATIONS = "1"
EXTRA_IMAGECMD:squashfs = "-comp zstd"

do_image[postfuncs] += "export_core_release"
export_core_release() {
    install -m 0644 ${IMAGE_ROOTFS}/etc/pantavisor/core-release.json \
        ${IMGDEPLOYDIR}/${IMAGE_LINK_NAME}.core-release.json
}
