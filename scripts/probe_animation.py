#!/usr/bin/env python3
"""Write a temporary WFF animation control, leaving production XML untouched.

Compare identical time-driven transforms in Scene and a stable complication.
This is diagnostic content, never a release watch face.
"""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from generate import node, group, text, ambient


def probe(parent, y, label):
    panel = node(parent, 'PartDraw', x=95, y=y-20, width=290, height=85)
    rectangle = node(panel, 'Rectangle', x=0, y=0, width=290, height=85)
    node(rectangle, 'Fill', color='#020704')
    text(parent, label, 100, y-18, 280, 20, 13)
    for index, direction in enumerate(('NONE', 'CLOCKWISE', 'POSITION')):
        x = 125 + index * 95
        marker = group(parent, 'probe_' + label + direction, x=x, y=y+15, width=42, height=42)
        marker.set('angle', '0')
        ambient(marker)
        moving = node(marker, 'Transform', target='x' if direction == 'POSITION' else 'angle',
                      value=f'[SECOND] % 4 < 2 ? {x if direction == "POSITION" else 0} : {x+30 if direction == "POSITION" else 90}')
        attrs = dict(duration=1, interpolation='LINEAR', fps=30)
        if direction != 'POSITION':
            attrs['angleDirection'] = direction
        node(moving, 'Animation', **attrs)
        drawing = node(marker, 'PartDraw', x=0, y=0, width=42, height=42)
        bar = node(drawing, 'Line', startX=21, startY=21, endX=21, endY=2)
        node(bar, 'Stroke', color='#FFC15C', thickness=5, cap='ROUND')
        text(parent, direction[:3], x-5, y+57, 52, 16, 12)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    document = ET.parse(Path(__file__).resolve().parents[1] / 'watchface/src/main/res/raw/watchface.xml')
    scene = document.getroot().find('Scene')
    phone = scene.find("ComplicationSlot[@slotId='2']")
    for bound in list(phone):
        if bound.tag.startswith('Bounding'):
            phone.remove(bound)
    node(phone, 'BoundingOval', x=0, y=0, width=480, height=480, outlinePadding=0)
    probe(scene, 255, 'SCENE')
    probe(phone.find("Complication[@type='RANGED_VALUE']"), 345, 'COMPLICATION')
    ET.indent(document.getroot())
    document.write(args.output, encoding='utf-8', xml_declaration=True)
