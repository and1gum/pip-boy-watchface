"""Calendar acceptance against production WFF, evaluated by the host renderer."""
import sys
import math
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render import Renderer


class CalendarTest(unittest.TestCase):
    def setUp(self):
        self.face = ET.parse(ROOT / 'watchface/src/main/res/raw/watchface.xml').getroot()
        self.renderer = Renderer()
        self.addCleanup(self.renderer.evaluate.close)
        self.slot = self.face.find(".//ComplicationSlot[@slotId='1']")

    def rows(self, title, text):
        values = {'COMPLICATION.TITLE': title, 'COMPLICATION.TEXT': text}
        def visit(element):
            if element.tag == 'Condition':
                expressions = {e.get('name'): e.text for e in element.findall('./Expressions/Expression')}
                selected = next((c for c in element.findall('Compare')
                                 if self.renderer.evaluate(expressions[c.get('expression')], values)), element.find('Default'))
                return visit(selected) if selected is not None else []
            if element.tag == 'TextCircular':
                return [self.renderer.content(element.find('Font'), values)]
            return [row for child in element for row in visit(child)]
        return visit(self.slot.find("Complication[@type='LONG_TEXT']"))

    def test_handoff_event_wraps_at_word_boundary(self):
        self.assertEqual(self.rows('18:00', 'Quick DS+GL Business Update: Strategy and Integration Progress'),
                         ['18:00 · Quick DS+GL', 'Business Update:…'])

    def test_calendar_tightens_gap_to_hour_marks_with_21px_font(self):
        arcs = self.slot.findall('.//TextCircular')
        self.assertEqual({float(a.get('width')) / 2 for a in arcs}, {194, 173})
        self.assertTrue(all(a.get('align') == 'CENTER' for a in arcs))
        for arc in arcs:
            expected = 21
            self.assertEqual(float(arc.find('Font').get('size')), expected)

    def test_calendar_rendering_stays_in_upper_band(self):
        layer = self.renderer.render(self.slot)
        left, top, right, bottom = layer.getbbox()
        x, y, width, height = 50, 22, 380, 160
        self.assertGreaterEqual(left, x)
        self.assertGreaterEqual(top, y)
        self.assertLessEqual(right, x + width)
        self.assertLessEqual(bottom, y + height)

    def test_calendar_text_fits_expanded_arc_clip(self):
        bounds = self.slot.find('BoundingArc')
        outer = float(bounds.get('width')) / 2
        inner = outer - float(bounds.get('thickness'))
        alpha = self.renderer.render(self.slot).getchannel('A')
        for y in range(alpha.height):
            for x in range(alpha.width):
                if alpha.getpixel((x, y)) > 100:
                    radius = math.hypot(x - 240, y - 240)
                    self.assertGreaterEqual(radius, inner)
                    self.assertLessEqual(radius, outer)

    def test_preview_measures_fractional_font_size_without_rounding(self):
        arc = self.slot.find('.//TextCircular')
        fractional = ET.fromstring(ET.tostring(arc.find('Font')))
        fractional.set('size', '17.5')
        font = self.renderer.font(fractional)
        self.assertEqual(font.size, 17.5)
        self.assertLessEqual(font.getlength('18:00 · Quick DS+GL Business Update:'), 182 * 2 * 3.141592653589793 / 3)

    def test_short_event_does_not_create_second_line_content(self):
        self.assertEqual(self.rows('09:30', 'Коротка зустріч'), ['09:30 · Коротка зустріч', ''])
        self.assertEqual(self.rows('', 'Коротка зустріч'), ['Коротка зустріч', ''])

    def test_last_row_uses_one_ellipsis_glyph_at_a_word_boundary(self):
        body = 'Обговорення плану розвитку команди українського проєкту та наступних важливих кроків'
        rows = self.rows('18:00', body)
        self.assertTrue(rows[1].endswith('…'))
        self.assertNotIn('...', rows[1])
        visible = (rows[0].removeprefix('18:00 · ') + ' ' + rows[1][:-1]).strip()
        self.assertTrue(body.startswith(visible + ' '))
        self.assertLessEqual(len(rows[1]), 23)
        self.assertTrue(all(arc.get('ellipsis') == 'FALSE' for arc in self.slot.findall('.//TextCircular')))

    def test_overlong_word_does_not_split_utf16_or_emoji(self):
        for body in ['Надзвичайнодовгесловобезпробілівуназві' * 3, '👩🏽\u200d💻' * 30]:
            self.assertEqual(self.rows('18:00', body), ['18:00', '…'])

    def test_calendar_and_time_do_not_overlap_at_extreme_times(self):
        for hour, minute in [('00', '00'), ('23', '59'), ('10', '09')]:
            r = Renderer(values={'HOUR_0_23_Z': hour, 'MINUTE_Z': minute}, complications={
                '1': {'type': 'LONG_TEXT', 'COMPLICATION.TITLE': '18:00',
                      'COMPLICATION.TEXT': 'WWW ' * 50}})
            try:
                r.render(self.face.find('Scene'))
                self.assertIsNone(ImageChops.multiply(r.masks['calendar'].filter(ImageFilter.MaxFilter(5)), r.masks['main_time']).getbbox(), hour)
            finally:
                r.evaluate.close()
