import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import ImageFont
ROOT=Path(__file__).resolve().parents[1]
class HealthPanelTest(unittest.TestCase):
 def test_pressure_has_real_provider_and_distinct_unknown_state(self):
  face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()
  slot=face.find(".//ComplicationSlot[@slotId='4']")
  self.assertIsNotNone(slot)
  self.assertTrue(slot.find('DefaultProviderPolicy').get('primaryProvider').endswith('.PressureSource'))
  for kind in ('RANGED_VALUE','EMPTY'):
   self.assertIsNotNone(slot.find(f"Complication[@type='{kind}']"))
  self.assertIsNotNone(face.find(".//Group[@name='pressure_trend']"))
 def test_large_pulse_and_icons_leave_sectors_and_weather_clear(self):
  face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()
  for part in face.findall(".//PartText[@name='pulse_tap']"):
   x,y,w,h=map(float,(part.get(k) for k in ('x','y','width','height')))
   self.assertGreaterEqual(x,146);self.assertLessEqual(x+w,239)
   self.assertGreaterEqual(y,335);self.assertLessEqual(y+h,400)
   font=part.find('.//Font');size=float(font.get('size'))
   self.assertGreaterEqual(size,48)
   metrics=ImageFont.truetype(str(ROOT/'watchface/src/main/res/font/terminal_bold.ttf'),round(size))
   self.assertLessEqual(metrics.getlength('199'),w)
   self.assertEqual(part.find('Launch').get('target'),'HEALTH_HEART_RATE')

 def test_solar_slots_have_separate_local_bounds_and_no_demo_times(self):
  face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()
  for slot_id in ('5','6'):
   slot=face.find(f".//ComplicationSlot[@slotId='{slot_id}']")
   self.assertIsNotNone(slot)
   self.assertTrue(slot.find('DefaultProviderPolicy').get('primaryProvider').endswith('.SolarSource'))
   self.assertLessEqual(float(slot.find('BoundingRoundBox').get('width')),100)
   self.assertIsNotNone(slot.find("Complication[@type='EMPTY']"))
   self.assertIsNotNone(slot.find('.//TextCircular//Parameter'))

 def test_pressure_number_is_inside_complication_clip_with_four_digit_room(self):
  face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()
  slot=face.find(".//ComplicationSlot[@slotId='4']")
  bounds=slot.find('BoundingRoundBox');bx,by,bw,bh=(float(bounds.get(k)) for k in ('x','y','width','height'))
  for part in slot.findall(".//PartText[@name='pressure_value']"):
   x,y,w,h=(float(part.get(k)) for k in ('x','y','width','height'))
   self.assertGreaterEqual(x,bx);self.assertGreaterEqual(y,337)
   self.assertLessEqual(x+w,bx+bw);self.assertLessEqual(y+h,by+bh)
   font=part.find('.//Font')
   self.assertEqual(int(font.get('size')),25)
   metrics=ImageFont.truetype(str(ROOT/'watchface/src/main/res/font/terminal_bold.ttf'),int(font.get('size')))
   self.assertLess(metrics.getlength('1100'),w-8)

 def test_solar_times_share_calendar_outer_radius_and_leave_angular_gap(self):
  import math
  face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()
  calendar=face.find(".//ComplicationSlot[@slotId='1']")
  outer=max(float(a.get('width'))/2 for a in calendar.findall('.//TextCircular'))
  for sid in ('5','6'):
   slot=face.find(f".//ComplicationSlot[@slotId='{sid}']")
   for arc in slot.findall('.//TextCircular'):
    self.assertEqual(float(arc.get('width'))/2,outer)
    self.assertEqual(float(arc.get('height'))/2,outer)
    font=ImageFont.truetype(str(ROOT/'watchface/src/main/res/font/terminal_bold.ttf'),21)
    center=abs((float(arc.get('startAngle'))+float(arc.get('endAngle')))/2)
    gap=center-math.degrees(font.getlength('07:15')/outer)/2-50
    self.assertGreaterEqual(gap,6)
    self.assertLessEqual(gap,9)

 def test_solar_icon_centers_follow_colon_rays_with_balanced_visible_gaps(self):
  import math
  from PIL import Image
  face=ET.parse(ROOT/'watchface/src/main/res/raw/watchface.xml').getroot()
  font=ImageFont.truetype(str(ROOT/'watchface/src/main/res/font/terminal_bold.ttf'),21)
  _,top,_,bottom=font.getbbox('07:15',anchor='ls')
  for sid in ('5','6'):
   slot=face.find(f".//ComplicationSlot[@slotId='{sid}']")
   arc=slot.find('.//TextCircular')
   theta=math.radians((float(arc.get('startAngle'))+float(arc.get('endAngle')))/2)
   u=(math.sin(theta),-math.cos(theta))
   icon=slot.find('.//PartImage')
   cx=float(icon.get('x'))+float(icon.get('width'))/2
   cy=float(icon.get('y'))+float(icon.get('height'))/2
   self.assertAlmostEqual((cx-240)*u[1]-(cy-240)*u[0],0,delta=.75)
   resource=icon.find('Image').get('resource')
   with Image.open(ROOT/'watchface/src/main/res/drawable'/f'{resource}.png') as source:
    im=source.resize((33,33),Image.Resampling.LANCZOS)
   outer=max((cx+x+.5-16.5-240)*u[0]+(cy+y+.5-16.5-240)*u[1]
             for y in range(33) for x in range(33) if im.getpixel((x,y))[3]>128)
   text_radius=float(arc.get('width'))/2
   self.assertAlmostEqual(text_radius-bottom-outer,218-(text_radius-top),delta=.75)
   bounds=slot.find('BoundingRoundBox')
   self.assertGreaterEqual(float(icon.get('x')),float(bounds.get('x')))
   self.assertLessEqual(float(icon.get('x'))+33,float(bounds.get('x'))+float(bounds.get('width')))
