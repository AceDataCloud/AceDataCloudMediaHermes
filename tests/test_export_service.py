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
                self.assertEqual(len(contract['tools']), 2 if source.get('task_path') else 1)
                self.assertFalse(set(contract['tools']) & set(source['tools']))
                self.assertIn('PLUGIN_SOURCE_REF:', files['.github/workflows/validate.yml'].decode())
                self.assertIn('ref: ' + 'a' * 40, files['.github/workflows/validate.yml'].decode())

    def test_nano_native_identity_and_recovery_follow_profile(self):
        files = exporter.build('nano-banana', 'a' * 40)
        image = files['image_provider.py'].decode()
        self.assertIn("return 'acedatacloud-single-nano-banana'", image)
        self.assertIn('acedatacloud_single_nano_banana_task', image)
        self.assertIn('/console/applications?', image)

    def test_all_canonical_services_have_source_profiles(self):
        expected = {p.stem for p in (ROOT / 'services').glob('*.json')}
        self.assertEqual(set(exporter.SERVICES), expected)

    def test_synchronous_profiles_have_one_tool_and_truthful_recovery(self):
        for service in ('face', 'google-search'):
            files = exporter.build(service, 'a' * 40)
            manifest = json.loads(files['plugin.yaml'])
            self.assertEqual(len(manifest['provides_tools']), 1)
            self.assertFalse(any(name.endswith('_task') for name in manifest['provides_tools']))
            self.assertIn('There is no task-query tool', files['README.md'].decode())
            self.assertIn('没有任务查询工具', files['readme/README_zh_Hans.md'].decode())

    def test_documented_historical_images_exist(self):
        import re
        for service in exporter.SERVICES:
            files = exporter.build(service, 'a' * 40)
            for name in ('README.md', 'readme/README_zh_Hans.md'):
                images = re.findall(r'assets/tutorial/(hermes-[^ )]+\.jpg)', files[name].decode())
                self.assertEqual(len(images), 1)
                self.assertTrue((ROOT / 'assets/tutorial' / images[0]).exists(), images[0])

    def test_paid_disclosure_does_not_assert_task_retrieval_is_charged(self):
        for service in exporter.SERVICES:
            files = exporter.build(service, 'a' * 40)
            self.assertIn('The primary operation spends paid Credits', files['README.md'].decode())
            self.assertNotIn('Every operation spends paid Credits', files['README.md'].decode())
            self.assertIn('主操作立即消耗 Credits', files['readme/README_zh_Hans.md'].decode())
