"""The fixed azimuth gap must fit every label emitted by Heading.label."""
import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from render import RES


class AzimuthTest(unittest.TestCase):
    def setUp(self):
        self.face = ET.parse(RES/'raw/watchface.xml').getroot()

    def test_azimuth_uses_date_font_and_circular_bottom_baseline(self):
        date = self.face.find(".//Group[@name='date']//Font")
        readout = self.face.find(".//Group[@name='azimuth_readout']//TextCircular")
        self.assertIsNotNone(readout)
        font = readout.find('Font')
        self.assertEqual(font.get('family'), date.get('family'))
        self.assertEqual(font.get('size'), date.get('size'))
        self.assertEqual(readout.get('direction'), 'COUNTER_CLOCKWISE')
        self.assertEqual(readout.get('align'), 'CENTER')
        self.assertEqual((float(readout.get('startAngle')) + float(readout.get('endAngle')))/2, 180)

    def test_gap_fits_longest_label_and_masks_both_scales(self):
        mask = self.face.find(".//Group[@name='azimuth_gap']//Arc")
        self.assertIsNotNone(mask)
        readout = self.face.find(".//Group[@name='azimuth_readout']//TextCircular")
        font = ImageFont.truetype(str(RES/'font'/(readout.find('Font').get('family')+'.ttf')),
                                 float(readout.find('Font').get('size')))
        labels = [f'{["N","NE","E","SE","S","SW","W","NW"][((n+22)//45)%8]} · {n:03d}°' for n in range(360)]
        maximum = max(map(font.getlength, labels))
        radius = float(readout.get('width'))/2
        expected = math.ceil(math.degrees((maximum+12)/radius))
        span = float(mask.get('endAngle'))-float(mask.get('startAngle'))
        self.assertEqual(span, expected)
        self.assertEqual(abs(float(readout.get('endAngle'))-float(readout.get('startAngle'))), span)
        stroke = mask.find('Stroke')
        self.assertEqual(stroke.get('cap'), 'BUTT', 'Round caps would enlarge the measured gap')
        mask_radius = float(mask.get('width'))/2
        thickness = float(stroke.get('thickness'))
        self.assertLessEqual(mask_radius-thickness/2, 210)
        self.assertGreaterEqual(mask_radius+thickness/2, 233)
        self.assertLessEqual(mask_radius-thickness/2, 218, 'The inner hour scale must also be cleared')

    def test_empty_azimuth_has_identical_font_and_arc(self):
        slot = self.face.find(".//ComplicationSlot[@slotId='3']")
        active = slot.find("Complication[@type='RANGED_VALUE']//Group[@name='azimuth_readout']//TextCircular")
        empty = slot.find("Complication[@type='EMPTY']//TextCircular")
        self.assertIsNotNone(active)
        for key in ('width', 'height', 'direction', 'startAngle', 'endAngle'):
            self.assertEqual(active.get(key), empty.get(key))
        for key in ('family', 'size'):
            self.assertEqual(active.find('Font').get(key), empty.find('Font').get(key))
