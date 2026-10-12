"""Exercise generated production WFF decisions, rather than a duplicate model."""
import math
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def evaluate(expression, values):
    expression = re.sub(r"\[([^]]+)\]", lambda m: repr(values[m[1]]), expression)
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", " not ", expression)
    expression = expression.replace("null", "None")
    return eval(expression, {"__builtins__": {}, "round": round, "floor": math.floor,
                             "clamp": lambda v, lo, hi: max(lo, min(v, hi))})


class WatchFaceTest(unittest.TestCase):
    def setUp(self):
        path = ROOT / "watchface/src/main/res/raw/watchface.xml"
        self.assertTrue(path.exists(), 'Production WFF has not been generated')
        self.face = ET.parse(path).getroot()

    def condition_cases(self, name):
        condition = self.face.find(f".//Condition[@name='{name}']")
        # Conditions cannot have arbitrary name attributes: the enclosing group is named.
        if condition is None:
            condition = self.face.find(f".//Group[@name='{name}']/Condition")
        self.assertIsNotNone(condition)
        expressions = {e.get('name'): e.text for e in condition.findall('./Expressions/Expression')}
        return [(expressions[c.get('expression')], c) for c in condition.findall('Compare')]

    def test_hr_boundaries_use_live_pulse_and_configured_thresholds(self):
        cases = self.condition_cases('heart_zones')
        base = {f'CONFIGURATION.hr{i}': v for i, v in enumerate([99, 110, 132, 165], 2)}
        for pulse, color in [(1, '409EF8'), (65, '409EF8'), (98, '409EF8'),
                             (99, '55B52C'), (109, '55B52C'), (110, 'F4B400'),
                             (128, 'F4B400'), (131, 'F4B400'), (132, 'FF730D'),
                             (164, 'FF730D'), (165, 'E52520'), (200, 'E52520')]:
            with self.subTest(pulse=pulse):
                selected = [c for e, c in cases if evaluate(e, base | {'HEART_RATE': pulse})]
                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0].find('.//Image').get('resource'), 'heart_' + color.lower())
        self.assertFalse(any(evaluate(e, base | {'HEART_RATE': 0}) for e, _ in cases))
        changed = base | {'CONFIGURATION.hr3': 125, 'HEART_RATE': 128}
        self.assertEqual([c.find('.//Image').get('resource') for e, c in cases if evaluate(e, changed)],
                         ['heart_f4b400'])

    def test_phone_battery_uses_numeric_complication_not_demo(self):
        slot = self.face.find(".//ComplicationSlot[@slotId='2']")
        self.assertIn('MobileBatteryComplicationService', slot.find('DefaultProviderPolicy').get('primaryProvider'))
        self.assertIn('RANGED_VALUE', slot.get('supportedTypes'))
        cases = self.condition_cases('phone_colors')
        for charge, color in [(0, 'E76F51'), (10, 'E76F51'), (11, 'FFC15C'),
                              (30, 'FFC15C'), (31, '91F894'), (100, '91F894')]:
            selected = [c for e, c in cases if evaluate(e, {'COMPLICATION.RANGED_VALUE_VALUE': charge})]
            self.assertEqual(len(selected), 1)
            self.assertIn(color.lower(), ET.tostring(selected[0], encoding='unicode').lower())

    def test_forecast_does_not_borrow_current_rain_probability(self):
        for offset in (3, 6):
            group = self.face.find(f".//Group[@name='weather_{offset}']")
            xml = ET.tostring(group, encoding='unicode')
            self.assertIn(f'WEATHER.HOURS.{offset}.IS_AVAILABLE', xml)
            self.assertIn(f'WEATHER.HOURS.{offset}.IS_DAY', xml)
            self.assertNotIn('CHANCE_OF_PRECIPITATION', xml)

    def test_weather_error_visible_even_when_no_data_and_clears_on_recovery(self):
        for offset in (0, 3, 6):
            cases = self.condition_cases(f'weather_error_{offset}')
            for available, failed in [(False, True), (True, True), (False, False), (True, False)]:
                values = {'WEATHER.IS_AVAILABLE': available, 'WEATHER.IS_ERROR': failed}
                selected = [c for e, c in cases if evaluate(e, values)]
                self.assertEqual(len(selected), int(failed))
                if failed:
                    self.assertEqual(selected[0].find('.//Font').text, '!')
        # The shared weather rectangle wins over overlapping complication targets.
        scene = self.face.find('Scene')
        target = scene.find("PartDraw[@name='weather_hit']")
        self.assertIsNotNone(target)
        self.assertEqual(target.find('Launch').get('target'), 'com.samsung.android.watch.weather')
        self.assertGreater(list(scene).index(target), list(scene).index(scene.find("ComplicationSlot[@slotId='3']")))

    def test_ambient_keeps_pressure_and_solar_but_hides_other_slots(self):
        active = self.face.find(".//Group[@name='active_only']")
        self.assertIsNotNone(active.find("./Variant[@mode='AMBIENT'][@value='0']"))
        slots = self.face.findall('./Scene/ComplicationSlot')
        self.assertEqual(len(slots), 6)
        for slot in slots:
            hidden=slot.find("./Variant[@mode='AMBIENT'][@value='0']")
            if slot.get('slotId') in ('4','5','6'):
                self.assertIsNone(hidden)
                for part in slot.findall('.//PartText')+slot.findall('.//PartImage')+slot.findall('.//PartDraw'):
                    target='alpha' if part.tag=='PartDraw' else 'tintColor'
                    self.assertIsNotNone(part.find(f"./Variant[@mode='AMBIENT'][@target='{target}']"))
            else:
                self.assertIsNotNone(hidden)
        for group in self.face.findall(".//Group"):
            if group.get('name', '').startswith('weather_'):
                self.assertIsNone(group.find("./Variant[@mode='AMBIENT'][@value='0']"))

    def test_compass_rotates_only_limb_and_preserves_real_north(self):
        slot = self.face.find(".//ComplicationSlot[@slotId='3']")
        self.assertIsNotNone(slot)
        self.assertIn('ua.and1gum.pipboy.compass', slot.find('DefaultProviderPolicy').get('primaryProvider'))
        bounds = slot.find('BoundingArc')
        self.assertIsNotNone(bounds, 'Use a ring so the compass does not intercept central status taps')
        self.assertEqual(bounds.get('width'), '480')
        self.assertEqual(bounds.get('height'), '480')
        self.assertEqual(bounds.get('thickness'), '32')
        self.assertEqual(bounds.get('startAngle'), '0')
        self.assertEqual(bounds.get('endAngle'), '359.99')
        rotor = slot.find(".//Group[@name='compass_limb']")
        self.assertIsNotNone(rotor)
        expression = rotor.find("Transform[@target='angle']").get('value')
        self.assertIsNone(rotor.find('Transform/Animation'), 'Provider supplies visual frames directly')
        self.assertEqual([s.get('slotId') for s in self.face.findall('./Scene/ComplicationSlot')], ['1','2','3','4','5','6'])
        for heading in (-1, 0, 1, 90, 180, 359, 361, 721):
            self.assertEqual(evaluate(expression, {'COMPLICATION.RANGED_VALUE_VALUE': heading, 'SECOND_MILLISECOND': 0}), -heading)
        self.assertIsNone(self.face.find(".//Group[@name='active_only']/Transform[@target='angle']"))
        empty = slot.find("Complication[@type='EMPTY']")
        self.assertIsNotNone(empty)
        self.assertIsNone(empty.find(".//Group[@name='compass_limb']"))

    def test_calendar_arcs_keep_upper_sector(self):
        slot = self.face.find(".//ComplicationSlot[@slotId='1']")
        arcs = slot.findall('.//TextCircular')
        self.assertGreaterEqual(len(arcs), 2)
        for arc in arcs:
            self.assertEqual(float(arc.get('startAngle')), -50)
            self.assertEqual(float(arc.get('endAngle')), 50)
        radii = sorted({float(a.get('width')) / 2 for a in arcs}, reverse=True)
        self.assertGreater(radii[0], radii[1])

    def test_resource_geometry_uses_integer_bounds_required_by_wff(self):
        for part in self.face.iter():
            if part.tag in ('PartImage', 'PartText', 'PartDraw', 'Group'):
                for key in ('x', 'y', 'width', 'height'):
                    self.assertRegex(part.get(key), r'^-?\d+$')

    def test_number_format_uses_android_decimalformat_patterns(self):
        for parameter in self.face.findall('.//Parameter'):
            expression = parameter.get('expression')
            self.assertNotRegex(expression, r'numberFormat\("[^"\n]*%')

    def test_text_suffixes_use_templates_instead_of_numeric_addition(self):
        for parameter in self.face.findall('.//Parameter'):
            expression = parameter.get('expression')
            self.assertNotRegex(expression, r'"\s*\+|\+\s*"')
        clock = self.face.find(".//PartText[@name='main_time']//Template")
        self.assertEqual(clock.text, '%s:%s')
        self.assertEqual(len(clock.findall('Parameter')), 2)

    def test_invalid_custom_zone_boundaries_do_not_assign_a_zone(self):
        values = {'HEART_RATE': 128, 'CONFIGURATION.hr2': 140, 'CONFIGURATION.hr3': 110,
                  'CONFIGURATION.hr4': 132, 'CONFIGURATION.hr5': 165}
        self.assertFalse(any(evaluate(e, values) for e, _ in self.condition_cases('heart_zones')))


if __name__ == '__main__':
    unittest.main()
