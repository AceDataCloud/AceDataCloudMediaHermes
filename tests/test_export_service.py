"""Generated consumers share runtime/contracts and cannot silently add services."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('export_service', ROOT / 'scripts/export_service.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ExportServiceTests(unittest.TestCase):
    def test_reproducible_minimal_service_contracts(self):
        for service in exporter.SERVICES:
            with self.subTest(service=service):
                files = exporter.build(service, 'a' * 40)
                self.assertEqual(files, exporter.build(service, 'a' * 40))
                contract = json.loads(files['services/' + service + '.json'])
                source = json.loads((ROOT / 'services' / (service + '.json')).read_text())
                for field in ('generate_schema', 'task_schema', 'generate_path', 'task_path', 'defaults'):
                    self.assertEqual(contract[field], source[field])
                self.assertEqual(files['client.py'], (ROOT / 'client.py').read_bytes())
                self.assertEqual(len([p for p in files if p.startswith('services/')]), 1)
                self.assertEqual(len(contract['tools']), 2)
                self.assertFalse(set(contract['tools']) & set(source['tools']))
                self.assertIn('PLUGIN_SOURCE_REF:', files['.github/workflows/validate.yml'].decode())
                self.assertIn('ref: ' + 'a' * 40, files['.github/workflows/validate.yml'].decode())

    def test_nano_native_identity_and_recovery_follow_profile(self):
        files = exporter.build('nano-banana', 'a' * 40)
        image = files['image_provider.py'].decode()
        self.assertIn("return 'acedatacloud-single-nano-banana'", image)
        self.assertIn('acedatacloud_single_nano_banana_task', image)
        self.assertIn('/console/applications?', image)
