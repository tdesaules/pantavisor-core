#!/usr/bin/env python3
"""Execute ARM64 component version checks without starting system services."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('component', type=Path)
args = parser.parse_args()
metadata = json.loads((args.component / 'component.json').read_text())
with (args.component / 'rootfs.squashfs').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == metadata['rootfsSha256']
with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary)
    root = directory / 'root'
    subprocess.run(['unsquashfs', '-no-progress', '-d', str(root), str(args.component / 'rootfs.squashfs')],
                   stdout=subprocess.DEVNULL, check=True)
    home = directory / 'home'
    home.mkdir()
    env = os.environ | {'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'config'), 'XDG_CACHE_HOME': str(home / 'cache')}
    if metadata['name'] != 'core': raise ValueError('Expected the Core component')
    if 'kubernetes-clients' not in metadata['features']: raise ValueError('Core must include Kubernetes clients')
    commands = [('bash', ['--version'], metadata['upstream']['bash']),
                ('kubectl', ['version', '--client', '-o', 'json'], metadata['upstream']['kubectl']),
                ('k0sctl', ['version'], metadata['upstream']['k0sctl']),
                ('k9s', ['version'], metadata['upstream']['k9s'])]
    for name, options, expected in commands:
        result = subprocess.run(['qemu-aarch64', '-L', str(root), str(root / 'usr/bin' / name), *options],
                                capture_output=True, text=True, env=env, timeout=60)
        if result.returncode or expected not in result.stdout + result.stderr:
            raise RuntimeError(name + ': ' + result.stdout + result.stderr)
        print('PASS:', name, expected)
