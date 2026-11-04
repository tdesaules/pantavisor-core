import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('component_package', ROOT / 'build/package.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ComponentTests(unittest.TestCase):
    def fixture(self, directory, secret=False, missing_tool=None):
        project = json.loads((ROOT / 'build/component.json').read_text())
        prefix = project['image'] + '-' + project['machine']
        for suffix in ('squashfs', 'manifest', 'spdx.tar.zst'):
            (directory / (prefix + '.' + suffix)).write_bytes(b'test payload')
        (directory / (prefix + '.core-release.json')).write_text(json.dumps({
            'version': (ROOT / 'VERSION').read_text().strip(),
            'kubernetes_tools': {name: project['upstream'][name] for name in ('kubectl', 'k0sctl', 'k9s')},
        }))
        with tarfile.open(directory / (prefix + '.tar.gz'), 'w:gz') as archive:
            member = tarfile.TarInfo('home/root/.ssh/authorized_keys' if secret else 'usr/bin/example')
            member.size = 4
            archive.addfile(member, io.BytesIO(b'test'))
            for name in ('kubectl', 'k0sctl', 'k9s'):
                if name == missing_tool: continue
                member = tarfile.TarInfo('usr/bin/' + name)
                member.size = 4
                member.mode = 0o755
                archive.addfile(member, io.BytesIO(b'test'))

        self.provenance(directory)

    def provenance(self, directory):
        files = {p.name: module.digest(p) for p in directory.iterdir() if p.name != 'build-provenance.json'}
        (directory / 'build-provenance.json').write_text(json.dumps({'schema': 1,
            'source': {'commit': 'fixture', 'dirty': True, 'treeSha256': module.provenance.snapshot(ROOT)}, 'files': files}))

    def test_independent_component_has_provenance_contract_and_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            result = module.package(directory, directory / 'output')
            self.assertEqual(result['schema'], 2)
            self.assertEqual(result['version'], (ROOT / 'VERSION').read_text().strip())
            self.assertEqual(result['architecture'], 'arm64')
            self.assertEqual(result['name'], 'core')
            self.assertIn('kubernetes-clients', result['features'])
            self.assertIn('runtime.json', result['files'])
            self.assertIn('lxc.conf.in', result['files'])
            self.assertEqual(result['rootfsSha256'], result['files']['rootfs.squashfs']['sha256'])
            self.assertNotIn('bsp', result)

    def test_credentials_are_rejected_before_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory, secret=True)
            with self.assertRaisesRegex(ValueError, 'Credentials'):
                module.package(directory, directory / 'output')
            self.assertFalse((directory / 'output').exists())

    def test_each_kubernetes_client_is_mandatory(self):
        for tool in ('kubectl', 'k0sctl', 'k9s'):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                self.fixture(directory, missing_tool=tool)
                with self.assertRaisesRegex(ValueError, tool):
                    module.package(directory, directory / 'output')
                self.assertFalse((directory / 'output').exists())

    def test_stale_core_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            project = json.loads((ROOT / 'build/component.json').read_text())
            release = directory / (project['image'] + '-' + project['machine'] + '.core-release.json')
            release.write_text(json.dumps({'version': (ROOT / 'VERSION').read_text().strip()}))
            self.provenance(directory)
            with self.assertRaisesRegex(ValueError, 'Kubernetes client versions'):
                module.package(directory, directory / 'output')
            self.assertFalse((directory / 'output').exists())

    def test_service_shell_syntax(self):
        for path in [*(ROOT / 'build').rglob('*'), *(ROOT / 'services').rglob('*')]:
            if path.is_file() and path.read_bytes().startswith(b'#!/bin/sh'):
                subprocess.run(['sh', '-n', str(path)], check=True)

    def test_payload_modified_after_build_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            next(directory.glob('*.squashfs')).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'payload changed'):
                module.package(directory, directory / 'output')

    def test_stale_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            path = directory / 'build-provenance.json'
            record = json.loads(path.read_text())
            record['source']['treeSha256'] = '0' * 64
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'Sources changed'):
                module.package(directory, directory / 'output')

    def test_failed_build_invalidates_previous_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            deploy = Path(temporary)
            (deploy / 'build-provenance.json').write_text('old attestation')
            with patch.object(module.provenance.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'build')):
                with self.assertRaises(subprocess.CalledProcessError):
                    module.provenance.run(ROOT, deploy, [], ['build'])
            self.assertFalse((deploy / 'build-provenance.json').exists())

    def test_publication_rejects_dirty_build_before_registry_access(self):
        spec = importlib.util.spec_from_file_location('publish', ROOT / 'build/publish.py')
        publish = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publish)
        with tempfile.TemporaryDirectory() as temporary:
            deploy = Path(temporary)
            self.fixture(deploy)
            module.package(deploy, deploy / 'output')
            with patch.object(publish.subprocess, 'run') as registry:
                with self.assertRaisesRegex(ValueError, 'clean source'):
                    publish.publish(deploy / 'output', 'ghcr.io/test/core')
                registry.assert_not_called()
                descriptor = deploy / 'output/component.json'
                metadata = json.loads(descriptor.read_text())
                metadata['source']['dirty'] = False
                descriptor.write_text(json.dumps(metadata))
                with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                    publish.publish(deploy / 'output', 'ghcr.io/test/core')
                registry.assert_not_called()

    def test_runtime_contract_is_board_independent(self):
        contract = json.loads((ROOT / 'runtime/contract.json').read_text())
        self.assertTrue(contract['id'].startswith('pantavisor-'))
        self.assertNotIn('ventuno', json.dumps(contract))
        self.assertNotIn('mmcblk', json.dumps(contract))
        self.assertNotIn('nvme', json.dumps(contract))
