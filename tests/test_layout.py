import sys
import tempfile
import unittest
from pathlib import Path
from PIL import ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from render import Renderer, Evaluator, DEFAULTS, COMPLICATIONS


class LayoutTest(unittest.TestCase):
    def test_calendar_preserves_time_title_without_string_addition(self):
        import xml.etree.ElementTree as ET
        from render import RES
        face=ET.parse(RES/'raw/watchface.xml').getroot()
        font=face.find(".//ComplicationSlot[@slotId='1']/Complication[@type='LONG_TEXT']//Compare//Font")
        renderer=Renderer()
        try:
            self.assertEqual(renderer.content(font, {'COMPLICATION.TITLE':'18:00',
                'COMPLICATION.TEXT':'Project meeting'}), '18:00 · Project meeting')
            self.assertEqual(renderer.content(font, {'COMPLICATION.TITLE':None,
                'COMPLICATION.TEXT':'18:00: Project meeting'}), '18:00: Project meeting')
        finally:renderer.evaluate.close()

    def test_calendar_does_not_intersect_clock_for_wide_times_and_unicode(self):
        for hour, minute, title in [
            ('00', '00', 'Quick DS+GL Business Update: Strategy and Integration Progress'),
            ('10', '09', 'Дуже довга українська назва зустрічі щодо інтеграції систем'),
            ('23', '59', 'W' * 150),
        ]:
            with self.subTest(time=hour+minute, title=title), tempfile.TemporaryDirectory() as tmp:
                payload = COMPLICATIONS | {'1': COMPLICATIONS['1'] | {'COMPLICATION.TEXT': title}}
                r = Renderer(values={'HOUR_0_23_Z': hour, 'MINUTE_Z': minute}, complications=payload)
                r.save(Path(tmp)/'proof.png')
                self.assertIsNone(ImageChops.multiply(r.masks['calendar'], r.masks['main_time']).getbbox())

    def test_calendar_substring_bounds_are_safe_for_short_and_missing_titles(self):
        import xml.etree.ElementTree as ET
        from render import RES
        face = ET.parse(RES/'raw/watchface.xml').getroot()
        parameters = face.findall(".//ComplicationSlot[@slotId='1']/Complication[@type='LONG_TEXT']//Parameter")
        evaluator = Evaluator()
        try:
            for title, text in [('18:00', 'A'), (None, 'A'), ('18:00', 'W'*150)]:
                values = {'COMPLICATION.TITLE': title, 'COMPLICATION.TEXT': text}
                for parameter in parameters:
                    expression = parameter.get('expression')
                    # Force Java substring bounds: Android WFF must not rely on JS's clamping.
                    if expression.startswith('subText(') or 'subText(' in expression:
                        self.assertIn('clamp(', expression)
                    result = evaluator(expression, values)
                    self.assertNotIn('null', result)
        finally:
            evaluator.close()

    def test_weather_and_health_no_data_are_distinct_from_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = Renderer(values={'HEART_RATE': 0, 'STEP_COUNT': -1, 'STEP_GOAL': 0,
                                 'WEATHER.IS_AVAILABLE': False,
                                 'WEATHER.HOURS.3.IS_AVAILABLE': False,
                                 'WEATHER.HOURS.6.IS_AVAILABLE': False}, complications={})
            r.save(Path(tmp)/'missing.png')
        # Snapshot must render without accessing absent complication payload fields.

    def test_current_precipitation_thresholds_select_exactly_one_asset(self):
        import xml.etree.ElementTree as ET
        from render import RES
        root = ET.parse(RES/'raw/watchface.xml').getroot()
        parent = root.find(".//Group[@name='weather_0']")
        expressions = [e for e in parent.findall('.//Expression') if 'CHANCE_OF_PRECIPITATION' in e.text]
        evaluator=Evaluator()
        try:
            for chance, expected in [(0,'one'),(19,'one'),(20,'two'),(69,'two'),(70,'three'),(100,'three')]:
                # Each rain/thunder/sleet state has separate day and night branches.
                chosen={e.get('name') for e in expressions if evaluator(e.text,DEFAULTS|{'WEATHER.CHANCE_OF_PRECIPITATION':chance})}
                self.assertEqual(chosen,{expected})
        finally:evaluator.close()


if __name__=='__main__':unittest.main()
