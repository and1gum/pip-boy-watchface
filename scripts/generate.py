#!/usr/bin/env python3
"""Build resource-only WFF and authored raster icons. No demo readings in XML."""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'watchface/src/main/res'
GREEN, AMBER, RED = '#91F894', '#FFC15C', '#E76F51'
AOD = '#FFFFFF'  # Neutral tint preserves authored colors; hardware dims the panel.
DIVIDER = '#579B5D'
FACE_SCALE = 1.0
MONO, DIGITAL = 'terminal_bold', 'digital_bold'
DATE_SIZE = 25
SECONDARY_SIZE = 21
CALENDAR_HALF_ANGLE = 50
OUTER_TEXT_RADIUS = 194
WEATHER_ICON_SIZE = 40
AZIMUTH_RADIUS = 226
DEVICE_ICON_SIZES = {'steps': (32, 44), 'watch': (30, 44), 'phone': (22, 44)}
DEVICE_ICON_SCALES = {'steps': .9, 'watch': .75, 'phone': .75}
STEPS_TARGET = 'ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.StepsLaunchActivity'
COMPASS_TARGET = 'com.samsung.android.watch.compass/com.samsung.android.watch.samsungcompass.ui.main.MainActivity'
NUMBER_BOUNDS = {'steps': (148,396,82,44), 'watch': (240,378,59,34), 'phone': (246,405,60,34)}
STRINGS = {'watch_face_name': 'Pip-Boy', 'calendar': 'Next calendar event',
           'phone_battery': 'Phone battery', 'compass': 'Compass', 'pressure':'Atmospheric pressure', 'sunrise':'Sunrise', 'sunset':'Sunset',
           **{f'hr{i}': f'Zone {i} starts at (bpm)' for i in range(2, 6)}}


def node(parent, tag, **attrs):
    if tag in ('PartImage', 'PartText', 'PartDraw', 'Group'):
        for key in ('x', 'y', 'width', 'height'):
            if key in attrs:
                attrs[key] = round(float(attrs[key]))
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def group(parent, name, x=0, y=0, width=480, height=480):
    return node(parent, 'Group', name=name, x=x, y=y, width=width, height=height)


def ambient(parent, target='alpha', value=0):
    node(parent, 'Variant', mode='AMBIENT', target=target, value=value)


def template(font, expression):
    t = node(font, 'Template')
    pattern, expressions = expression if isinstance(expression, tuple) else ('%s', [expression])
    t.text = pattern
    for value in expressions:
        node(t, 'Parameter', expression=value)


def text(parent, value, x, y, width, height, size, color=GREEN, expression=False,
         family=MONO, aod=False, name=None):
    attrs = dict(x=x, y=y, width=width, height=height)
    if name:
        attrs['name'] = name
    p = node(parent, 'PartText', **attrs)
    if aod:
        ambient(p, 'tintColor', AOD)
    t = node(p, 'Text', align='CENTER', ellipsis='TRUE', maxLines=1)
    f = node(t, 'Font', family=family, size=size, color=color)
    if expression:
        template(f, value)
    else:
        f.text = value
    return p


def circular(parent, value, radius, start, end, size=SECONDARY_SIZE, color=GREEN,
             expression=False, direction='CLOCKWISE', center=(240, 240), align='CENTER',
             bounds=(0,0,480,480), launch=None, name=None):
    x,y,width,height = bounds
    p = node(parent, 'PartText', x=x, y=y, width=width, height=height)
    if name:
        p.set('name', name)
    if launch:
        node(p, 'Launch', target=launch)
    t = node(p, 'TextCircular', centerX=center[0]-x, centerY=center[1]-y,
             width=radius * 2, height=radius * 2, startAngle=start,
             endAngle=end, direction=direction, align=align, ellipsis='TRUE')
    f = node(t, 'Font', family=MONO, size=size, color=color)
    if expression:
        template(f, value)
    else:
        f.text = value
    return p


def image(parent, resource, x, y, width, height, aod=False):
    p = node(parent, 'PartImage', x=x, y=y, width=width, height=height)
    if aod:
        ambient(p, 'tintColor', AOD)
    node(p, 'Image', resource=resource)
    return p


def draw(parent):
    return node(parent, 'PartDraw', x=0, y=0, width=480, height=480)


def line(parent, x1, y1, x2, y2, color, thickness=1):
    l = node(draw(parent), 'Line', startX=x1, startY=y1, endX=x2, endY=y2)
    node(l, 'Stroke', color=color, thickness=thickness, cap='ROUND')


def ellipse(parent, x, y, width, height, color, thickness=1, fill=False):
    e = node(draw(parent), 'Ellipse', x=x, y=y, width=width, height=height)
    node(e, 'Fill' if fill else 'Stroke', **({'color': color} if fill else
                                          {'color': color, 'thickness': thickness}))


def arc(parent, radius, start, end, color, thickness=9, fraction=None,
        direction='CLOCKWISE', cap='ROUND'):
    a = node(draw(parent), 'Arc', centerX=240, centerY=240, width=radius*2,
             height=radius*2, startAngle=start, endAngle=end, direction=direction)
    node(a, 'Stroke', color=color, thickness=thickness, cap=cap)
    if fraction is not None:
        node(a, 'Transform', target='endAngle', value=f'{start} + ({end-start}) * ({fraction})')


def condition(parent, branches):
    c = node(parent, 'Condition')
    ex = node(c, 'Expressions')
    for name, expression in branches:
        e = node(ex, 'Expression', name=name)
        e.text = expression
    return c, {name: node(c, 'Compare', expression=name) for name, _ in branches}


def sector(parent, device, radius, start, end, color, fraction=None):
    """One uninterrupted visible stroke, with separate local touch surfaces."""
    target = STEPS_TARGET if device == 'steps' else 'BATTERY_STATUS'
    direction = 'CLOCKWISE' if end > start else 'COUNTER_CLOCKWISE'
    owner = parent
    if fraction is not None:
        _, cases = condition(parent, [('filled', f'({fraction}) > 0')])
        owner = cases['filled']
    part = node(owner, 'PartDraw', x=0, y=0, width=480, height=480,
                name=device+'_sector_visual')
    shape = node(part, 'Arc', centerX=240, centerY=240, width=radius*2,
                 height=radius*2, startAngle=start, endAngle=end, direction=direction)
    node(shape, 'Stroke', color=color, thickness=9, cap='ROUND')
    if fraction is not None:
        node(shape, 'Transform', target='endAngle',
             value=f'{start} + ({end-start}) * clamp(({fraction}), 0, 1)')
    # The faint hit surfaces remain active over the entire sector, including
    # its unfilled portion. They do not paint the progress stroke.
    count = math.ceil(abs(end-start) / 5)
    for index in range(count):
        a = start + (end-start) * index/count
        b = start + (end-start) * (index+1)/count
        samples = [polar(radius, angle) for angle in (a, (a+b)/2, b)]
        x = math.floor(min(p[0] for p in samples)-7)
        y = math.floor(min(p[1] for p in samples)-7)
        right = math.ceil(max(p[0] for p in samples)+7)
        bottom = math.ceil(max(p[1] for p in samples)+7)
        part = node(parent, 'PartDraw', x=x, y=y, width=right-x, height=bottom-y,
                    name=device+'_sector_tap')
        rect = node(part, 'Rectangle', x=0, y=0, width=right-x, height=bottom-y)
        node(rect, 'Fill', color='#01000000')
        node(part, 'Launch', target=target)


def polar(radius, angle):
    rad = math.radians(angle)
    return 240 + radius*math.sin(rad), 240 - radius*math.cos(rad)


def slot(scene, slot_id, label, types, box, provider=None, system='EMPTY', default_type='EMPTY'):
    s = node(scene, 'ComplicationSlot', slotId=slot_id, displayName=label,
             supportedTypes=types, x=0, y=0, width=480, height=480)
    ambient(s)
    attrs = dict(defaultSystemProvider=system, defaultSystemProviderType=default_type)
    if provider:
        attrs.update(primaryProvider=provider, primaryProviderType=default_type)
    node(s, 'DefaultProviderPolicy', **attrs)
    node(s, 'BoundingRoundBox', x=box[0], y=box[1], width=box[2], height=box[3],
         outlinePadding=2, cornerRadius=10)
    return s


def azimuth_geometry():
    """Measure every label emitted by the eight-direction Heading.label API."""
    font = ImageFont.truetype(str(RES/'font'/f'{MONO}.ttf'), DATE_SIZE)
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    labels = [f'{directions[((n+22)//45)%8]} · {n:03d}°' for n in range(360)]
    longest = max(labels, key=font.getlength)
    width = font.getlength(longest)
    # Six logical pixels of side padding; square ends keep the gap exact.
    gap = math.ceil(math.degrees((width+12)/AZIMUTH_RADIUS))
    return gap, longest, width


def calendar_layout(calendar):
    """Generate bounded word wrapping using supported WFF 3 string operations.

    Cuts occur only at spaces, never inside a UTF-16 pair or combining sequence.
    Ordered Compare branches choose the last fitting word boundary. The final
    row reserves one glyph for U+2026 and truncates only at word boundaries.
    """
    geometry = [(OUTER_TEXT_RADIUS, SECONDARY_SIZE), (173, SECONDARY_SIZE)]
    capacities = []
    for radius, size in geometry:
        font = ImageFont.truetype(str(RES / 'font' / f'{MONO}.ttf'), round(size * 10))
        capacities.append(int(math.radians(2 * CALENDAR_HALF_ANGLE) * radius / (font.getlength('M') / 10)))
    n1, n2 = capacities
    body, title = '[COMPLICATION.TEXT]', '[COMPLICATION.TITLE]'
    length = f'textLength({body})'
    has_title = f'{title} != null && textLength({title}) > 0'
    prefix = f'({has_title} ? textLength({title}) + 3 : 0)'
    room = f'clamp({n1} - {prefix}, 0, {n1})'

    def substring(start, end):
        return f'subText({body}, clamp({start}, 0, {length}), clamp({end}, 0, {length}))'

    def boundary(position):
        char = substring(str(position), str(position + 1))
        return f'({char} == " " || {char} == "\u00a0")'

    def rows(parent, first_end, second_start, fits=False):
        first = ('%s%s%s', [f'{has_title} ? {title} : ""',
                 f'({has_title}) && ({first_end} > 0) ? " · " : ""', substring('0', str(first_end))])
        circular(parent, first, geometry[0][0], -CALENDAR_HALF_ANGLE, CALENDAR_HALF_ANGLE, size=SECONDARY_SIZE, expression=True, align='CENTER')
        if fits:
            second = '""'
        else:
            remaining_fits = f'{length} - {second_start} <= {n2}'
            last_boundary = str(second_start)
            for cut in range(1, n2):
                position = second_start + cut
                last_boundary = f'({boundary(position)} ? {position} : {last_boundary})'
            end = f'({remaining_fits} ? {length} : {last_boundary})'
            second = ('%s%s', [substring(str(second_start), end),
                               f'{remaining_fits} ? "" : "…"'])
        circular(parent, second, geometry[1][0], -CALENDAR_HALF_ANGLE, CALENDAR_HALF_ANGLE, size=SECONDARY_SIZE, expression=True, align='CENTER')

    for kind in ('LONG_TEXT', 'SHORT_TEXT'):
        complication = node(calendar, 'Complication', type=kind)
        _, payload = condition(complication, [('event', f'{body} != null && {length} > 0 && {body} != "Немає майбутніх подій" && {body} != "No upcoming events"')])
        branches = [('fits', f'{length} <= {room}')]
        branches.extend((f'break_{cut}', f'{cut} <= {room} && {boundary(cut)}')
                        for cut in range(n1, 0, -1))
        wrapping, cases = condition(payload['event'], branches)
        rows(cases['fits'], length, 0, fits=True)
        for cut in range(n1, 0, -1):
            rows(cases[f'break_{cut}'], cut, cut + 1)
        rows(node(wrapping, 'Default'), 0, 0)
        circular(node(complication.find('Condition'), 'Default'), 'NO UPCOMING EVENTS',
                 geometry[0][0], -CALENDAR_HALF_ANGLE, CALENDAR_HALF_ANGLE, size=SECONDARY_SIZE, align='CENTER')
    circular(node(calendar, 'Complication', type='EMPTY'), 'CALENDAR UNAVAILABLE',
             geometry[0][0], -CALENDAR_HALF_ANGLE, CALENDAR_HALF_ANGLE, size=SECONDARY_SIZE, align='CENTER')
    return capacities


def solar_icon(setting):
 s=4
 im=Image.new('RGBA',(64*s,64*s));d=ImageDraw.Draw(im)
 color='#F49A60' if setting else '#FFC15C'
 def box(v): return tuple(round(n*s) for n in v)
 def stroke(coords,width=3):
  d.line(box(coords),fill=color,width=round(width*s))
  r=width/2
  for x,y in ((coords[0],coords[1]),(coords[2],coords[3])): d.ellipse(box((x-r,y-r,x+r,y+r)),fill=color)
 cy=43 if setting else 34
 horizon=39 if setting else 43
 d.ellipse(box((18,cy-14,46,cy+14)),fill=color)
 d.rectangle(box((0,horizon+1,64,64)),fill=(0,0,0,0))
 for angle in ((205,270,335) if setting else (195,230,270,310,345)):
  a=math.radians(angle)
  x1,y1=32+18*math.cos(a),cy+18*math.sin(a)
  x2,y2=32+23*math.cos(a),cy+23*math.sin(a)
  if y2<horizon-3: stroke((x1,y1,x2,y2),2.5)
 stroke((7,horizon,57,horizon),3)
 if setting:
  stroke((18,46,46,46),2.5)
  stroke((25,52,39,52),2.5)
 else:
  stroke((23,50,41,50),2.5)
 im=im.resize((128,128),Image.Resampling.LANCZOS)
 name='sunset_horizon' if setting else 'sunrise_horizon'
 im.resize((64,64),Image.Resampling.LANCZOS).save(RES/'drawable'/f'{name}.png')


def solar_icon_position(label, angle, size=33):
    """Align the icon with the time's colon and balance the visible radial gaps.

    The surrounding compass circle is radius 218. Measure authored pixels,
    excluding transparent padding, so sunrise and sunset get the same spacing.
    """
    radial = (math.sin(math.radians(angle)), -math.cos(math.radians(angle)))
    font = ImageFont.truetype(str(RES/'font'/f'{MONO}.ttf'), SECONDARY_SIZE)
    _, top, _, bottom = font.getbbox('07:15', anchor='ls')
    text_outer = OUTER_TEXT_RADIUS - top
    text_inner = OUTER_TEXT_RADIUS - bottom
    gap = 218 - text_outer
    with Image.open(RES/'drawable'/f'{label}_horizon.png') as source:
        icon = source.resize((size, size), Image.Resampling.LANCZOS)
    extent = max((x+.5-size/2)*radial[0] + (y+.5-size/2)*radial[1]
                 for y in range(size) for x in range(size)
                 if icon.getpixel((x,y))[3] > 128)
    radius = text_inner - gap - extent
    cx, cy = polar(radius, angle)
    return cx-size/2, cy-size/2


def assets():
    """Supersampled original icons; output at 64px to keep WFF memory low."""
    (RES / 'drawable').mkdir(exist_ok=True)
    solar_icon(False)
    solar_icon(True)
    scale = 4
    def canvas():
        im = Image.new('RGBA', (64*scale, 64*scale))
        return im, ImageDraw.Draw(im)
    def box(b):
        return tuple(v*scale for v in b)
    def save(im, name):
        im.resize((64, 64), Image.Resampling.LANCZOS).save(RES/'drawable'/f'{name}.png')
    def sun(d, cx=23, cy=22):
        d.ellipse(box((cx-9, cy-9, cx+9, cy+9)), fill='#FFC15C')
        for angle in range(0, 360, 45):
            a=math.radians(angle)
            d.line(box((cx+12*math.cos(a), cy+12*math.sin(a),
                        cx+16*math.cos(a), cy+16*math.sin(a))), fill='#FFC15C', width=2*scale)
    def moon(d):
        d.ellipse(box((8, 6, 34, 32)), fill='#DCE7F4')
        d.ellipse(box((17, 2, 39, 25)), fill=(0, 0, 0, 0))
    def cloud(d, dark=False):
        color = '#8497A6' if dark else '#E6ECE8'
        d.ellipse(box((14, 23, 37, 45)), fill=color)
        d.ellipse(box((27, 16, 50, 45)), fill=color)
        d.rounded_rectangle(box((9, 32, 57, 47)), radius=7*scale, fill=color)
    for state in range(16):
        for day in (0, 1):
            for drops in ((1, 2, 3) if state in (4, 6, 9, 10, 12) else (0,)):
                im,d=canvas()
                if state in (1, 8, 14):
                    sun(d) if day else moon(d)
                if state not in (0, 1, 8):
                    cloud(d, state in (4, 6, 9, 10, 12))
                if state == 0:
                    f=ImageFont.truetype(str(RES/'font'/f'{MONO}.ttf'), 38*scale)
                    d.text((23*scale, 6*scale), '?', font=f, fill=GREEN)
                if state in (4, 6, 9, 10, 12):
                    for x in [32] if drops == 1 else ([23, 41] if drops == 2 else [18,32,46]):
                        # Filled 8x12px droplets stay readable at the 36px WFF size.
                        points = [(x, 49)] + [
                            (x+4*math.cos(math.radians(angle)),
                             57+4*math.sin(math.radians(angle)))
                            for angle in range(180, -1, -10)]
                        d.polygon([tuple(v*scale for v in p) for p in points], fill='#65B8FF')
                if state in (5, 7, 10, 11):
                    for x in (20, 43):
                        for angle in (0, 60, 120):
                            a=math.radians(angle)
                            d.line(box((x-4*math.cos(a),55-4*math.sin(a),x+4*math.cos(a),55+4*math.sin(a))),
                                   fill='#E6F4FF', width=scale)
                if state == 9:
                    d.polygon([tuple(v*scale for v in p) for p in [(34,31),(26,45),(34,43),(29,55),(43,38),(34,40)]], fill='#FFD64F')
                if state in (3, 13, 15):
                    for y in (51, 57):
                        d.line(box((13, y, 52, y)), fill='#A1B8AC', width=scale)
                save(im, f'weather_{state}_{day}_{drops}')
    for color in ('409ef8', '55b52c', 'f4b400', 'ff730d', 'e52520', '91f894'):
        im,d=canvas()
        pts=[]
        for i in range(181):
            a=2*math.pi*i/180
            pts.append(((32+1.65*16*math.sin(a)**3)*scale,
                        (30-1.65*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a)))*scale))
        if color == '91f894':
            d.line(pts+[pts[0]], fill='#'+color, width=2*scale)
        else:
            d.polygon(pts, fill='#'+color)
        save(im, 'heart_'+color)
    for device, (width, height) in DEVICE_ICON_SIZES.items():
        # Match the display aspect ratio; avoid scaling a padded square sprite.
        im = Image.new('RGBA', (width*scale, height*scale))
        d = ImageDraw.Draw(im)
        if device == 'steps':
            for sole, toes in [((1,11,13,31), (3,1,11,9)),
                               ((19,23,31,43), (21,13,29,21))]:
                d.ellipse(box(sole), fill='white')
                d.ellipse(box(toes), fill='white')
        elif device == 'watch':
            for strap in [(10,1,20,10), (10,34,20,43)]:
                d.rounded_rectangle(box(strap), radius=2*scale, outline='white', width=2*scale)
            d.ellipse(box((1,8,29,36)), fill=(0,0,0,0), outline='white', width=2*scale)
            d.line(box((15,15,15,22,21,25)), fill='white', width=2*scale)
            d.ellipse(box((14,21,16,23)), fill='white')
        else:
            d.rounded_rectangle(box((1,1,21,43)), radius=3*scale, outline='white', width=2*scale)
            d.line(box((8,5,14,5)), fill='white', width=scale)
            d.line(box((8,38,14,38)), fill='white', width=scale)
        im.resize((width*2,height*2), Image.Resampling.LANCZOS).save(RES/'drawable'/f'{device}.png')


def device_icon(parent, device, radius, sector_start, color=GREEN):
    width, height = DEVICE_ICON_SIZES[device]
    # Project the actual sector head vertically onto the 9–3 o'clock axis.
    center_x = round(polar(radius, sector_start)[0])
    part = image(parent, device, center_x-width/2, 240-height/2, width, height)
    part.set('tintColor', color)
    part.set('scaleX', str(DEVICE_ICON_SCALES[device]))
    part.set('scaleY', str(DEVICE_ICON_SCALES[device]))
    part.set('pivotX', '0.5')
    part.set('pivotY', '0.5')
    node(part, 'Launch', target=STEPS_TARGET if device == 'steps' else 'BATTERY_STATUS')
    return part


def battery(parent, value, radius, start, end, device, name):
    g=group(parent, name)
    cases=[('critical', f'{value} <= 10'), ('low', f'{value} > 10 && {value} <= 30'),
           ('healthy', f'{value} > 30')]
    _, branches=condition(g,cases)
    for key,color in [('critical',RED),('low',AMBER),('healthy',GREEN)]:
        p=branches[key]
        sector(p,device,radius,start,end,'#29'+color[1:])
        sector(p,device,radius,start,end,color,fraction=f'clamp({value}/100, 0, 1)')
        device_icon(p, device, radius, start, color)
        circular(p,('%s%%', [f'numberFormat("0", {value})']),radius,end+26,end-3,
                 color=color,expression=True,direction='COUNTER_CLOCKWISE',
                 bounds=NUMBER_BOUNDS[device], launch=COMPASS_TARGET, name=device+'_tap')


def weather(scene, offset, x):
    x -= 12  # Balance the single steps ring against both battery rings.
    prefix='WEATHER' if offset == 0 else f'WEATHER.HOURS.{offset}'
    g=group(scene,f'weather_{offset}')
    label='"NOW"' if offset == 0 else f'icuText("HH:mm", (floor([UTC_TIMESTAMP] / 3600000) + {offset}) * 3600000)'
    label_part=text(g,label,x-50,250,100,27,SECONDARY_SIZE,expression=True,aod=True,name=f'weather_open_{offset}')
    _,available=condition(g,[('available',f'[{prefix}.IS_AVAILABLE]')])
    p=available['available']
    text(p,('%s°', [f'numberFormat("0", [{prefix}.TEMPERATURE])']),x-15,280,76,37,DATE_SIZE,expression=True,aod=True)
    _,states=condition(p,[(f'state_{i}',f'[{prefix}.CONDITION] == {i}') for i in range(16)])
    for state,parent in states.items():
        i=int(state.split('_')[1])
        _,days=condition(parent,[('day',f'[{prefix}.IS_DAY]'),('night',f'![{prefix}.IS_DAY]')])
        for daytime,dayparent in days.items():
            day=1 if daytime == 'day' else 0
            default_drops=3 if i == 4 else (1 if i == 12 else 2)
            if i not in (4,6,9,10,12):
                default_drops=0
            if offset == 0 and i in (4,6,9,10,12):
                _,probabilities=condition(dayparent,[('one','[WEATHER.CHANCE_OF_PRECIPITATION] < 20'),
                    ('two','[WEATHER.CHANCE_OF_PRECIPITATION] >= 20 && [WEATHER.CHANCE_OF_PRECIPITATION] < 70'),
                    ('three','[WEATHER.CHANCE_OF_PRECIPITATION] >= 70')])
                for key,drops in [('one',1),('two',2),('three',3)]:
                    image(probabilities[key],f'weather_{i}_{day}_{drops}',x-53,278,WEATHER_ICON_SIZE,WEATHER_ICON_SIZE,aod=True)
            else:
                image(dayparent,f'weather_{i}_{day}_{default_drops}',x-53,278,WEATHER_ICON_SIZE,WEATHER_ICON_SIZE,aod=True)
    image(node(p.find('Condition'), 'Default'), 'weather_0_1_0', x-53,278,WEATHER_ICON_SIZE,WEATHER_ICON_SIZE,aod=True)
    # No weather is distinct from a zero-degree reading.
    default=node(g.find('Condition'),'Default')
    text(default,'—',x-15,280,76,37,DATE_SIZE,aod=True)
    image(default,'weather_0_1_0',x-53,278,WEATHER_ICON_SIZE,WEATHER_ICON_SIZE,aod=True)
    # A failed request can leave IS_AVAILABLE=false: show the failure independently
    # of availability, preserving any data that the runtime still considers usable.
    status=group(g,f'weather_error_{offset}')
    _,error=condition(status,[('failed','[WEATHER.IS_ERROR]')])
    text(error['failed'],'!',x+40,254,14,20,15,AMBER,aod=True)


def generate():
    assets()
    azimuth_gap, azimuth_longest, azimuth_width = azimuth_geometry()
    gap_start, gap_end = 180 - azimuth_gap/2, 180 + azimuth_gap/2
    root=ET.Element('WatchFace',width='480',height='480')
    configs=node(root,'UserConfigurations')
    for i,default in enumerate([99,110,132,165],2):
        c=node(configs,'ListConfiguration',id=f'hr{i}',displayName=f'hr{i}',defaultValue=default)
        # Up to 100 list entries per WFF setting; +/- 40 bpm preserves exact integer thresholds.
        for value in range(default-40,default+41):
            STRINGS[f'bpm_{value}']=str(value)
            node(c,'ListOption',id=value,displayName=f'bpm_{value}')
    scene=node(root,'Scene',backgroundColor='#020704')
    bezel=group(scene,'bezel')
    ellipse(bezel,8,8,464,464,'#315839',1)
    ambient(bezel,'tintColor',AOD)
    date=group(scene,'date')
    weekday='[DAY_OF_WEEK] == 1 ? "SUN" : [DAY_OF_WEEK] == 2 ? "MON" : [DAY_OF_WEEK] == 3 ? "TUE" : [DAY_OF_WEEK] == 4 ? "WED" : [DAY_OF_WEEK] == 5 ? "THU" : [DAY_OF_WEEK] == 6 ? "FRI" : "SAT"'
    text(date,('%s %s', [weekday, '[DAY_Z]']),120,94,240,33,DATE_SIZE,expression=True,aod=True)
    # Restore handoff time size so the original calendar radii remain clear.
    clock=group(scene,'clock')
    text(clock,('%s:%s', ['[HOUR_0_23_Z]', '[MINUTE_Z]']),60,127,360,110,110,
         family=DIGITAL,expression=True,aod=True,name='main_time')
    for offset,x in [(0,136),(3,240),(6,344)]:
        weather(scene,offset,x)
    active=group(scene,'active_only')
    ambient(active)
    for angle in range(0,360,30):
        if gap_start <= angle <= gap_end:
            continue
        x1,y1=polar(211,angle);x2,y2=polar(218,angle)
        line(active,x1,y1,x2,y2,AMBER,2)
    steps=group(active,'steps')
    device_icon(steps,'steps',194,261)
    sector(steps,'steps',194,261,209,'#2991F894')
    _,step_cases=condition(steps,[('available','[STEP_COUNT] >= 0 && [STEP_GOAL] > 0')])
    sector(step_cases['available'],'steps',194,261,209,GREEN,fraction='clamp([STEP_COUNT]/[STEP_GOAL], 0, 1)')
    _,counts=condition(steps,[('count_available','[STEP_COUNT] >= 0')])
    circular(counts['count_available'],'numberFormat("#,##0", [STEP_COUNT])',194,209,184,size=SECONDARY_SIZE,
             direction='COUNTER_CLOCKWISE',expression=True,
             bounds=NUMBER_BOUNDS['steps'], launch=COMPASS_TARGET, name='steps_tap')
    circular(node(steps.findall('Condition')[-1],'Default'),'—',194,209,184,size=SECONDARY_SIZE,
             direction='COUNTER_CLOCKWISE', bounds=NUMBER_BOUNDS['steps'], launch=COMPASS_TARGET, name='steps_tap')
    battery(active,'[BATTERY_PERCENT]',166,100.536,158,'watch','watch_colors')
    heart_taps=group(active,'heart_rate_taps')
    icon=image(heart_taps,'heart_91f894',109,345,33,33)
    heart=group(heart_taps,'heart_zones')
    hr='[HEART_RATE]'
    thresholds=[f'round([CONFIGURATION.hr{i}])' for i in range(2,6)]
    branches=[('zone1',f'{hr} > 0 && {hr} < {thresholds[0]}')]
    for i in range(1,4):
        branches.append((f'zone{i+1}',f'{hr} >= {thresholds[i-1]} && {hr} < {thresholds[i]}'))
    branches.append(('zone5',f'{hr} >= {thresholds[-1]} && {hr} > 0'))
    ordered=' && '.join(f'{thresholds[i]} < {thresholds[i+1]}' for i in range(3))
    branches=[(name, f'({ordered}) && ({expression})') for name,expression in branches]
    _,zones=condition(heart,branches)
    for i,color in enumerate(['409ef8','55b52c','f4b400','ff730d','e52520'],1):
        icon=image(zones[f'zone{i}'],'heart_'+color,109,345,33,33)
    pulse_condition,pulse=condition(heart_taps,[('pulse_available','[HEART_RATE] > 0')])
    reading=text(pulse['pulse_available'],'numberFormat("0", round([HEART_RATE]))',146,340,91,58,48,expression=True,name='pulse_tap')
    node(reading,'Launch',target='HEALTH_HEART_RATE')
    reading=text(node(pulse_condition,'Default'),'—',146,340,91,58,48,name='pulse_tap')
    node(reading,'Launch',target='HEALTH_HEART_RATE')
    line(active,108,328,345,328,DIVIDER,1)
    line(active,240,337,240,386,DIVIDER,1)
    # Hands share system time, update only in active mode, and remain secondary.
    for name,value,length,tail,width,color in [
        ('hour','[HOUR_0_11_MINUTE]*30',147,17,6,'#D9FFC15C'),
        ('minute','[MINUTE_SECOND]*6',203,22,4,'#D9FFC15C'),
        ('second','[SECOND]*6',190,33,2.4,'#FF3939')]:
        hand=group(active,'hand_'+name)
        node(hand,'Transform',target='angle',value=value)
        if name == 'second':
            # Leave the counterweight interior transparent, including its shaft.
            line(hand,240,260.5,240,240-length,color,width)
            line(hand,240,271.5,240,240+tail,color,width)
            ellipse(hand,235,261,10,10,color,1.8)
        else:
            line(hand,240,240+tail,240,240-length,color,width)
    ellipse(active,235.5,235.5,9,9,'#020704',fill=True)
    ellipse(active,235.5,235.5,9,9,AMBER,2)
    # Scene-level complication slots are required by the WFF schema.
    calendar=slot(scene,'1','calendar','LONG_TEXT SHORT_TEXT EMPTY',(50,22,380,160),
        system='NEXT_EVENT',default_type='LONG_TEXT')
    # WFF shares rendering and touch bounds: follow the text arcs rather than
    # covering the time and system status indicators with a rectangular target.
    calendar.remove(calendar.find('BoundingRoundBox'))
    node(calendar, 'BoundingArc', centerX=240, centerY=240, width=420, height=420,
         thickness=50, startAngle=-CALENDAR_HALF_ANGLE, endAngle=CALENDAR_HALF_ANGLE, outlinePadding=0)
    capacities = calendar_layout(calendar)
    # Samsung WFF renders native ellipsis as three separate periods.
    for arc_text in calendar.findall('.//TextCircular'):
        arc_text.set('ellipsis', 'FALSE')
    phone=slot(scene,'2','phone_battery','RANGED_VALUE EMPTY',(210,210,250,245),
        provider='com.weartools.phonebattcomp/com.weartools.phonebattcomp.complication.MobileBatteryComplicationService',
        default_type='RANGED_VALUE')
    ranged=node(phone,'Complication',type='RANGED_VALUE')
    battery(ranged,'[COMPLICATION.RANGED_VALUE_VALUE]',194,99,158,'phone','phone_colors')
    for kind in ('EMPTY',):
        c=node(phone,'Complication',type=kind)
        device_icon(c,'phone',194,99)
        sector(c,'phone',194,99,158,'#2991F894')
        circular(c,'—',194,184,155,direction='COUNTER_CLOCKWISE', bounds=NUMBER_BOUNDS['phone'], launch=COMPASS_TARGET, name='phone_tap')
    compass=slot(scene,'3','compass','RANGED_VALUE EMPTY',(145,418,190,55),
        provider='ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.CompassSource',
        default_type='RANGED_VALUE')
    compass.remove(compass.find('BoundingRoundBox'))
    # The limb needs only the outer ring. A full disk also catches mode-icon taps.
    node(compass, 'BoundingArc', centerX=240, centerY=240, width=480, height=480,
         thickness=32, startAngle=0, endAngle=359.99, outlinePadding=0)
    # Preserve slot declaration order so existing Samsung bindings remain stable.

    payload=node(compass,'Complication',type='RANGED_VALUE')
    limb=group(payload,'compass_limb')
    rotation=node(limb,'Transform',target='angle',value='-[COMPLICATION.RANGED_VALUE_VALUE]')
    ellipse(limb,22,22,436,436,'#68B974',1)
    for angle in range(0,360,5):
        if angle % 90 == 0:
            x,y=polar(225,angle)
            cardinal=text(limb,{0:'N',90:'E',180:'S',270:'W'}[angle],x-13,y-14,26,28,16,
                          color=AMBER if angle == 0 else '#68B974')
            upright=node(cardinal,'Transform',target='angle',value='[COMPLICATION.RANGED_VALUE_VALUE]')
        else:
            x1,y1=polar(224 if angle % 30 == 0 else 228,angle)
            x2,y2=polar(232,angle)
            line(limb,x1,y1,x2,y2,'#8C91F894' if angle % 30 == 0 else '#4091F894',1)
    # The fixed gap clears rotating ticks AND the fixed hour-scale radius.
    # BUTT ends avoid widening the measured 38-degree sector with round caps.
    for target in (payload, node(compass, 'Complication', type='EMPTY')):
        mask = group(target, 'azimuth_gap')
        arc(mask, 221, gap_start, gap_end, '#020704', 32, cap='BUTT')
        readout = group(target, 'azimuth_readout')
        circular(readout, '[COMPLICATION.TEXT]' if target is payload else '—',
                 AZIMUTH_RADIUS, gap_end, gap_start, size=DATE_SIZE,
                 direction='COUNTER_CLOCKWISE', expression=target is payload,
                 bounds=(140,438,200,38), launch=COMPASS_TARGET)
    # Keep weather labels visually above complication rendering.
    for offset in (0,3,6):
        owner=scene.find(f"Group[@name='weather_{offset}']")
        label=owner.find(f"PartText[@name='weather_open_{offset}']")
        owner.remove(label)
        scene.append(label)
    # The phone complication's bounds intercept the watch icon beneath it.
    # Raise the watch sector, icon and numbers with their color conditions.
    lifted = group(scene, 'watch_icon_taps')
    ambient(lifted)
    _, icon_cases = condition(lifted, [
        ('critical', '[BATTERY_PERCENT] <= 10'),
        ('low', '[BATTERY_PERCENT] > 10 && [BATTERY_PERCENT] <= 30'),
        ('healthy', '[BATTERY_PERCENT] > 30')])
    original = active.find("Group[@name='watch_colors']/Condition")
    for key, target in icon_cases.items():
        owner = original.find(f"Compare[@expression='{key}']")
        for part in list(owner):
            owner.remove(part)
            target.append(part)
    # Step numbers can also overlap the phone slot's rectangular bounds.
    active.remove(steps)
    ambient(steps)
    scene.append(steps)
    active.remove(heart_taps)
    ambient(heart_taps)
    scene.append(heart_taps)
    # Give the sector touch surfaces priority at their boundary with pulse.
    scene.remove(steps)
    scene.append(steps)
    pressure=slot(scene,'4','pressure','RANGED_VALUE EMPTY',(247,326,110,71),
        provider='ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.PressureSource',default_type='RANGED_VALUE')
    for kind in ('RANGED_VALUE','EMPTY'):
        payload=node(pressure,'Complication',type=kind)
        line(payload,254,356,254,380,'#1B3821',8)
        for y in (354,362,370,379):
            line(payload,263,y,267,y,DIVIDER,1)
        text(payload,'mm',279,362,42,26,SECONDARY_SIZE).find('Text').set('align','START')
        if kind=='EMPTY':
            text(payload,'—',279,337,73,32,DATE_SIZE,name='pressure_missing').find('Text').set('align','START')
            continue
        text(payload,'%s',279,337,73,32,DATE_SIZE,expression=False,name='pressure_value')
        payload.find("PartText[@name='pressure_value']/Text").set('align','START')
        value=payload.find("PartText[@name='pressure_value']//Font")
        value.text=None
        template(value,'[COMPLICATION.TEXT]')
        trend=group(payload,'pressure_trend')
        _,states=condition(trend,[('rising','[COMPLICATION.TITLE] == "up"'),
            ('falling','[COMPLICATION.TITLE] == "down"'),('stable','[COMPLICATION.TITLE] == "steady"')])
        default=node(trend.find('Condition'),'Default')
        for owner,color,symbol in [(states['rising'],AMBER,'↗'),(states['falling'],'#65B8FF','↘'),
                                   (states['stable'],GREEN,'→'),(default,'#53665B',None)]:
            shape=node(draw(owner),'Line',startX=254,startY=380,endX=254,endY=380)
            node(shape,'Transform',target='endY',value='380 - 24*clamp(([COMPLICATION.RANGED_VALUE_VALUE]-950)/100,0,1)')
            node(shape,'Stroke',color=color,thickness=8,cap='ROUND')
            if symbol:
                indicator=node(owner,'PartDraw',x=244,y=331,width=20,height=19,name='pressure_direction')
                segments={
                    '↗':[(4,14,15,3),(7,3,15,3),(15,3,15,11)],
                    '↘':[(4,3,15,14),(7,14,15,14),(15,14,15,6)],
                    '→':[(3,9,17,9),(11,3,17,9),(17,9,11,15)]}[symbol]
                for x1,y1,x2,y2 in segments:
                    shape=node(indicator,'Line',startX=x1,startY=y1,endX=x2,endY=y2)
                    node(shape,'Stroke',color=color,thickness=2,cap='ROUND')
    # Both solar times are calculated for the local calendar day by the companion.
    for slot_id,label,x,start,end,field in (
        ('5','sunrise',18,-80.5,-54.5,'TEXT'),
        ('6','sunset',380,54.5,80.5,'TITLE')):
        solar_width=90 if label=='sunrise' else 82
        icon_x, icon_y = solar_icon_position(label, (start+end)/2)
        solar=slot(scene,slot_id,label,'SHORT_TEXT EMPTY',(x,126,solar_width,106),
            provider='ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.SolarSource',default_type='SHORT_TEXT')
        for kind in ('SHORT_TEXT','EMPTY'):
            payload=node(solar,'Complication',type=kind)
            circular(payload,f'[COMPLICATION.{field}]' if kind=='SHORT_TEXT' else '—',
                     OUTER_TEXT_RADIUS,start,end,size=SECONDARY_SIZE,expression=kind=='SHORT_TEXT',bounds=(x,126,solar_width,106),
                     launch='ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.EnvironmentActivity')
            icon=image(payload,label+'_horizon',icon_x,icon_y,33,33)
            node(icon,'Launch',target='ua.and1gum.pipboy.compass/ua.and1gum.pipboy.compass.EnvironmentActivity')
    # Pressure and today's solar events remain readable in AOD at the same
    # full tint as the active date and weather; hardware controls dimming.
    for slot_id in ('4','5','6'):
        owner=scene.find(f"ComplicationSlot[@slotId='{slot_id}']")
        owner.remove(owner.find("Variant[@mode='AMBIENT'][@target='alpha']"))
        for part in owner.findall('.//PartText')+owner.findall('.//PartImage')+owner.findall('.//PartDraw'):
            if part.tag=='PartDraw':
                ambient(part,'alpha',255)
            else:
                ambient(part,'tintColor',AOD)
    # One weather target between the clock, steps, batteries and heart rate.
    # Nonzero alpha retains a drawable surface for Samsung hit testing.
    hit=node(scene,'PartDraw',x=70,y=242,width=305,height=78,name='weather_hit')
    ambient(hit)
    rectangle=node(hit,'Rectangle',x=0,y=0,width=305,height=78)
    node(rectangle,'Fill',color='#01000000')
    node(hit,'Launch',target='com.samsung.android.watch.weather')
    # All visible composition shares the face center, including Scene-level slots.
    # Keep a small edge inset for circular text and round hour-marker caps.
    for element in scene:
        element.set('scaleX', str(FACE_SCALE))
        element.set('scaleY', str(FACE_SCALE))
    ET.indent(root)
    ET.ElementTree(root).write(RES/'raw/watchface.xml',encoding='utf-8',xml_declaration=True)
    strings=ET.Element('resources')
    for key,value in sorted(STRINGS.items()):
        node(strings,'string',name=key).text=value
    ET.indent(strings)
    ET.ElementTree(strings).write(RES/'values/strings.xml',encoding='utf-8',xml_declaration=True)
    print(f'Azimuth longest {azimuth_longest!r}: {azimuth_width}px; gap {azimuth_gap} degrees.')
    print(f'Generated WFF 3; measured calendar capacities {capacities}; no sample readings.')


if __name__ == '__main__':
    generate()
