"""Visible device icons align to the 9–3 line and their own sector heads."""
import math
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT/'watchface/src/main/res'


class DeviceIconTest(unittest.TestCase):
    def setUp(self):
        self.face = ET.parse(RES/'raw/watchface.xml').getroot()

    def test_all_device_icons_center_on_horizontal_axis_above_sector_heads(self):
        heads = {'steps': (194,261), 'watch': (166,100.536), 'phone': (194,99)}
        for device, (radius, angle) in heads.items():
            parts = [
                p for p in self.face.findall('.//PartImage') if p.find('Image').get('resource') == device]
            self.assertTrue(parts)
            endpoint_x = 240+radius*math.sin(math.radians(angle))
            endpoint_y = 240-radius*math.cos(math.radians(angle))
            for part in parts:
                x,y,w,h = [float(part.get(k)) for k in ('x','y','width','height')]
                with self.subTest(device=device):
                    self.assertEqual(y+h/2,240)
                    self.assertLessEqual(abs(x+w/2-endpoint_x),0.5)
                    self.assertEqual(h,44)
                    self.assertGreaterEqual(endpoint_y-4.5-(y+h),2.5)

    def test_watch_and_phone_have_clearance_at_maximum_height(self):
        def first(resource):
            return next(p for p in self.face.findall('.//PartImage') if p.find('Image').get('resource')==resource)
        watch,phone,steps = map(first,('watch','phone','steps'))
        self.assertGreaterEqual(float(phone.get('x'))-(float(watch.get('x'))+float(watch.get('width'))),3)
        self.assertGreaterEqual(float(steps.get('x')),32, 'Leave the 9 oclock yellow tick visible')
        self.assertGreaterEqual(float(watch.get('width')),30)
        self.assertGreaterEqual(float(phone.get('height'))/float(phone.get('width')),2)

    def test_authored_assets_use_visible_tall_silhouettes(self):
        for device in ('steps','watch','phone'):
            with Image.open(RES/'drawable'/f'{device}.png') as image:
                self.assertGreater(image.height,image.width)
                bounds=image.getchannel('A').getbbox()
                self.assertGreaterEqual((bounds[3]-bounds[1])/image.height,.9)
