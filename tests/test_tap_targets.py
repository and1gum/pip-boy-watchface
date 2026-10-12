"""Visible tap targets are local and retain their native destination."""
import unittest
import math
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class TapTargetTest(unittest.TestCase):
    def setUp(self):
        self.face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()

    def test_azimuth_opens_samsung_compass_with_local_bounds(self):
        for group in self.face.findall(".//Group[@name='azimuth_readout']"):
            part=group.find('PartText')
            self.assertIsNotNone(part.find('Launch'))
            self.assertEqual(part.find('Launch').get('target'),'com.samsung.android.watch.compass/com.samsung.android.watch.samsungcompass.ui.main.MainActivity')
            self.assertGreaterEqual(float(part.get('y')),438)
            self.assertLess(float(part.get('height')),50)
            arc=part.find('TextCircular')
            self.assertEqual(float(part.get('x'))+float(arc.get('centerX')),240)
            self.assertEqual(float(part.get('y'))+float(arc.get('centerY')),240)

    def test_icons_and_numbers_use_requested_destinations(self):
        destinations={'steps':'ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.StepsLaunchActivity',
                      'watch':'BATTERY_STATUS','phone':'BATTERY_STATUS'}
        for part in self.face.findall('.//PartImage'):
            resource=part.find('Image').get('resource')
            if resource in destinations:
                self.assertIsNotNone(part.find('Launch'),resource)
                self.assertEqual(part.find('Launch').get('target'),destinations[resource])
        numbers=self.face.findall(".//PartText[@name='steps_tap']")+self.face.findall(".//PartText[@name='watch_tap']")+self.face.findall(".//PartText[@name='phone_tap']")
        self.assertGreaterEqual(len(numbers),9)
        for part in numbers:
            self.assertIsNotNone(part.find('Launch'))
            self.assertEqual(part.find('Launch').get('target'),
                'com.samsung.android.watch.compass/com.samsung.android.watch.samsungcompass.ui.main.MainActivity')
            self.assertLess(float(part.get('height')),60)
            self.assertLess(float(part.get('width')),200)

    def test_visible_sector_segments_have_small_local_native_targets(self):
        for device, target in [('steps', 'ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.StepsLaunchActivity'),
                               ('watch', 'BATTERY_STATUS'), ('phone', 'BATTERY_STATUS')]:
            parts = self.face.findall(f".//PartDraw[@name='{device}_sector_tap']")
            self.assertGreaterEqual(len(parts), 10, device)
            for part in parts:
                self.assertEqual(part.find('Launch').get('target'), target)
                self.assertIsNone(part.find('Arc'))
                self.assertEqual(part.find('Rectangle/Fill').get('color'),'#01000000')
                self.assertLess(float(part.get('width')), 45)
                self.assertLess(float(part.get('height')), 45)


    def test_sector_visuals_are_continuous_and_separate_from_touch(self):
        for device in ('steps','watch','phone'):
            visuals=self.face.findall(f".//PartDraw[@name='{device}_sector_visual']")
            self.assertGreaterEqual(len(visuals),2)
            for part in visuals:
                self.assertIsNone(part.find('Launch'))
                arc=part.find('Arc')
                self.assertGreater(abs(float(arc.get('endAngle'))-float(arc.get('startAngle'))),45)
                self.assertEqual(arc.find('Stroke').get('cap'),'ROUND')

    def test_only_pulse_numbers_open_system_heart_rate(self):
        icons = [p for p in self.face.findall('.//PartImage')
                 if p.find('Image').get('resource').startswith('heart_')]
        self.assertEqual(len(icons),6)
        for icon in icons:
            self.assertIsNone(icon.find('Launch'))
        readings=self.face.findall(".//PartText[@name='pulse_tap']")
        self.assertEqual(len(readings),2)
        for part in readings:
            self.assertEqual(part.find('Launch').get('target'),'HEALTH_HEART_RATE')
        scene=self.face.find('Scene');heart=scene.find("Group[@name='heart_rate_taps']")
        self.assertIsNotNone(heart.find("Variant[@mode='AMBIENT'][@value='0']"))

    def test_sector_endpoints_are_not_intercepted_by_number_targets(self):
        for device, radius, start, end in [('steps',194,261,209), ('watch',166,100.536,158), ('phone',194,99,158)]:
            numbers = self.face.findall(f".//PartText[@name='{device}_tap']")
            segments = self.face.findall(f".//PartDraw[@name='{device}_sector_tap']")
            def contains(part, px, py):
                x,y,w,h = [float(part.get(k)) for k in ('x','y','width','height')]
                return x <= px <= x+w and y <= py <= y+h
            for ratio in (0, .25, .5, .75, 1):
                angle = math.radians(start+(end-start)*ratio)
                px,py = 240+radius*math.sin(angle), 240-radius*math.cos(angle)
                with self.subTest(device=device, ratio=ratio):
                    self.assertTrue(any(contains(p,px,py) for p in segments))
                    self.assertFalse(any(contains(p,px,py) for p in numbers))

    def test_steps_sector_has_priority_over_neighboring_pulse_target(self):
        scene=self.face.find('Scene')
        self.assertGreater(list(scene).index(scene.find("Group[@name='steps']")),
                           list(scene).index(scene.find("Group[@name='heart_rate_taps']")))

    def test_watch_icon_is_above_phone_slot_hit_area(self):
        scene=self.face.find('Scene')
        lifted=scene.find("Group[@name='watch_icon_taps']")
        self.assertIsNotNone(lifted)
        self.assertGreater(list(scene).index(lifted),list(scene).index(scene.find("ComplicationSlot[@slotId='3']")))
        self.assertEqual(len(lifted.findall('.//PartImage')),3)

    def test_calendar_touch_bounds_follow_expanded_text_arcs_and_leave_time_free(self):
        calendar = self.face.find("./Scene/ComplicationSlot[@slotId='1']")
        self.assertIsNone(calendar.find('BoundingRoundBox'))
        bounds = calendar.find('BoundingArc')
        self.assertIsNotNone(bounds)
        outer = float(bounds.get('width')) / 2
        inner = outer - float(bounds.get('thickness'))
        self.assertEqual(float(bounds.get('centerX')), 240)
        self.assertEqual(float(bounds.get('centerY')), 240)
        self.assertEqual(float(bounds.get('height')), outer * 2)
        self.assertEqual(float(bounds.get('startAngle')), -50)
        self.assertEqual(float(bounds.get('endAngle')), 50)
        self.assertGreaterEqual(inner, 146, 'Keep the main time outside the target')
        self.assertLessEqual(outer, 210, 'Keep the text target inside the hour marks')
        self.assertEqual(calendar.findall('.//Launch'), [])

    def test_no_full_face_part_launch_and_slot_order_unchanged(self):
        for part in self.face.findall('.//Launch/..'):
            self.assertFalse(float(part.get('width'))>=480 and float(part.get('height'))>=480)
        self.assertEqual([s.get('slotId') for s in self.face.findall('./Scene/ComplicationSlot')],['1','2','3','4','5','6'])
        self.assertEqual(self.face.find(".//PartDraw[@name='weather_hit']/Launch").get('target'),'com.samsung.android.watch.weather')

    def test_single_weather_rectangle_covers_weather_and_leaves_neighbors_clear(self):
        scene = self.face.find('Scene')
        hits = [p for p in scene.findall('PartDraw') if p.get('name','').startswith('weather_hit')]
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        x,y,w,h = [float(hit.get(k)) for k in ('x','y','width','height')]
        self.assertEqual((x,y,w,h), (70,242,305,78))
        self.assertGreater(y, 237)  # Clock bottom.
        self.assertLess(y+h, 322)  # Heart outline top.
        self.assertIsNotNone(hit.find("Variant[@mode='AMBIENT'][@value='0']"))
        for slot in scene.findall('ComplicationSlot'):
            self.assertGreater(list(scene).index(hit), list(scene).index(slot))
        for offset, center in ((0,124),(3,228),(6,332)):
            label=self.face.find(f".//PartText[@name='weather_open_{offset}']")
            self.assertEqual(float(label.get('x'))+float(label.get('width'))/2,center)
            for px,py in ((center,260),(center-33,298),(center+12,298)):
                self.assertTrue(x <= px <= x+w and y <= py <= y+h)
            self.assertIsNone(self.face.find(f".//PartText[@name='weather_open_{offset}']/Launch"))
        for radius, start, end in ((194,209,261),(166,100.536,158),(194,99,158)):
            for i in range(101):
                angle=math.radians(start+(end-start)*i/100)
                px,py=240+radius*math.sin(angle),240-radius*math.cos(angle)
                self.assertFalse(x-4.5 <= px <= x+w+4.5 and y-4.5 <= py <= y+h+4.5)
