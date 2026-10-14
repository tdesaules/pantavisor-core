# Ship the matching generator so diagnostic host keys can be generated offline.
SBINCOMMANDS:append = " dropbearkey"
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI:append = " file://core-localoptions.h"

do_configure:prepend() {
    install -m 0644 ${WORKDIR}/core-localoptions.h ${B}/localoptions.h
}
