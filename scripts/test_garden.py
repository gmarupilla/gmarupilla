import copy
from datetime import date, timedelta
import unittest
import xml.etree.ElementTree as ET

import garden


class GardenTests(unittest.TestCase):
    def setUp(self):
        self.day = date(2026, 10, 13)
        self.state = {'version': 1, 'plots': {}, 'requests': {}, 'gardeners': {}, 'last_planted': {}, 'composted': 0}

    def issue(self, number=1, user='visitor', plot='A1', seed='Oak'):
        return {'number': number, 'user': {'login': user}, 'body': f'### Plot\n\n{plot}\n\n### Seed\n\n{seed}\n'}

    def test_retry_cannot_plant_twice(self):
        issue = self.issue()
        garden.process(self.state, [issue], self.day)
        saved = copy.deepcopy(self.state)
        garden.process(self.state, [issue], self.day)
        self.assertEqual(saved, self.state)
        self.assertTrue(self.state['requests']['1']['accepted'])

    def test_two_visitors_cannot_overwrite_a_plot(self):
        garden.process(self.state, [self.issue(), self.issue(2, 'someone-else')], self.day)
        self.assertEqual(self.state['plots']['A1']['user'], 'visitor')
        self.assertFalse(self.state['requests']['2']['accepted'])

    def test_daily_limit_resets_at_utc_day_boundary(self):
        garden.process(self.state, [self.issue(), self.issue(2, 'Visitor', 'B2')], self.day)
        self.assertFalse(self.state['requests']['2']['accepted'])
        garden.process(self.state, [self.issue(3, 'visitor', 'B2')], self.day + timedelta(days=1))
        self.assertTrue(self.state['requests']['3']['accepted'])

    def test_expired_plot_can_be_replanted(self):
        garden.process(self.state, [self.issue()], self.day)
        garden.process(self.state, [self.issue(2, 'next-person')], self.day + timedelta(days=21))
        self.assertEqual(self.state['plots']['A1']['user'], 'next-person')
        self.assertEqual(self.state['composted'], 1)

    def test_malformed_requests_do_not_change_plots(self):
        issues = [self.issue(1, seed='Oak\n$(touch /tmp/unsafe)'), self.issue(2, plot='Z9'), self.issue(3, user='bot[bot]')]
        garden.process(self.state, issues, self.day)
        self.assertEqual(self.state['plots'], {})
        self.assertTrue(all(not r['accepted'] for r in self.state['requests'].values()))

    def test_svg_and_links_cover_all_plots_and_seed_types(self):
        for i, seed in enumerate(garden.SEEDS):
            self.state['plots'][garden.PLOTS[i]] = {'seed': seed, 'user': 'visitor', 'planted': str(self.day - timedelta(days=5))}
        for offset in (0, 1, 4, 21):
            ET.fromstring(garden.draw(self.state, self.day + timedelta(days=offset)))
        for kind in ('terrain', 'yield', 'dry'):
            ET.fromstring(garden.cover('Name & test', 'Illustration', kind))
        readme = garden.readme(self.state, self.day)
        self.assertEqual(readme.count('template=plant.yml'), 18)
        self.assertIn('plot=D6', readme)
        self.assertNotIn('plot=A1)', readme)


if __name__ == '__main__':
    unittest.main()
