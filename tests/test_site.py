import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


class PublicSiteTests(unittest.TestCase):
    def test_public_build_has_only_synthetic_records_and_relative_assets(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('build_site', root / 'scripts/build_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'site'
            module.build(output)
            states = json.loads((output / 'demo/states.json').read_text())
            self.assertEqual(len(states), 14)
            for state in states.values():
                self.assertTrue(state['demo'])
                self.assertEqual(state['profile']['payload']['name'], '小林')
                self.assertTrue(all('合成演示' in r['payload']['note'] for r in state['logs']))
            self.assertFalse(list(output.rglob('*.sqlite*')))
            html = (output / 'demo/index.html').read_text()
            self.assertIn('src="./preview.js"', html)
            self.assertNotIn('src="/app.js"', html)
            self.assertIn('lang="zh-CN"', html)


if __name__ == '__main__':
    unittest.main()
