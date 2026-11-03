import copy
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from generator import professional
from generator.config import ConfigError
from generator.themes import get_theme

ROOT = Path(__file__).resolve().parents[1]


class ProfessionalStatsTests(unittest.TestCase):
    def setUp(self):
        self.stats = professional.load(ROOT / 'professional-stats.json')

    def test_exported_metrics_in_all_variants(self):
        for mode in ('dark', 'light'):
            for mobile in (False, True):
                svg = professional.render(self.stats, get_theme('deep-sky', mode, {}), mobile)
                tree = ET.fromstring(svg)
                desc = tree.find('{http://www.w3.org/2000/svg}desc').text
                for text in ('200 PRs opened', '176 PRs merged', '161 PRs reviewed', '29 repositories',
                             '2025-11-03 to 2026-11-03'):
                    self.assertIn(text, desc)

    def test_missing_metric_is_not_zero(self):
        self.stats['personal_activity']['prs_merged'] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stats.json'
            path.write_text(json.dumps(self.stats))
            loaded = professional.load(path)
        svg = professional.render(loaded, get_theme('deep-sky', 'dark', {}))
        self.assertIn('N/A PRs merged', svg)

    def test_percentages_keep_original_denominator(self):
        self.assertEqual(professional.language_shares(self.stats, 2),
                         [('Go', 28.8), ('Jupyter Notebook', 27.3)])

    def test_invalid_export_is_rejected(self):
        for change in ('negative', 'dates', 'percentages'):
            stats = copy.deepcopy(self.stats)
            if change == 'negative':
                stats['personal_activity']['prs_opened'] = -1
            elif change == 'dates':
                stats['period']['start_utc'] = stats['period']['end_utc']
            else:
                stats['languages']['distribution_percent']['Go'] = 110
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'stats.json'
                path.write_text(json.dumps(stats))
                with self.assertRaises(ConfigError):
                    professional.load(path)


if __name__ == '__main__':
    unittest.main()
