#!/usr/bin/env python3
"""Host proof images from production WFF. Synthetic readings only, never device evidence.

This renderer implements the subset emitted by generate.py, not the Wear OS engine.
Use physical screenshots to verify font metrics, provider binding and AOD behavior.
"""
from pathlib import Path
import argparse
import json
import math
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'watchface/src/main/res'
DEFAULTS={
    'DAY_OF_WEEK':1,'DAY_Z':'11',
    'HOUR_0_23_Z':'10','MINUTE_Z':'09','SECOND':24,'HOUR_0_11_MINUTE':10.15,
    'MINUTE_SECOND':9.4,'UTC_TIMESTAMP':1791713340000,'STEP_COUNT':6240,'STEP_GOAL':8000,
    'BATTERY_PERCENT':15,'HEART_RATE':128,
    'CONFIGURATION.hr2':99,'CONFIGURATION.hr3':110,'CONFIGURATION.hr4':132,'CONFIGURATION.hr5':165,
    'WEATHER.IS_AVAILABLE':True,'WEATHER.IS_ERROR':False,'WEATHER.CONDITION':14,
    'WEATHER.IS_DAY':True,'WEATHER.TEMPERATURE':12,'WEATHER.CHANCE_OF_PRECIPITATION':20,
    'WEATHER.HOURS.3.IS_AVAILABLE':True,'WEATHER.HOURS.3.IS_DAY':True,
    'WEATHER.HOURS.3.CONDITION':12,'WEATHER.HOURS.3.TEMPERATURE':14,
    'WEATHER.HOURS.6.IS_AVAILABLE':True,'WEATHER.HOURS.6.IS_DAY':True,
    'WEATHER.HOURS.6.CONDITION':6,'WEATHER.HOURS.6.TEMPERATURE':13,
}
COMPLICATIONS={
    '3':{'type':'RANGED_VALUE','COMPLICATION.RANGED_VALUE_VALUE':42,'COMPLICATION.TEXT':'NE · 042°'},
    '1':{'type':'LONG_TEXT','COMPLICATION.TITLE':'18:00',
         'COMPLICATION.TEXT':'Quick DS+GL Business Update: Strategy and Integration Progress'},
    '2':{'type':'RANGED_VALUE','COMPLICATION.RANGED_VALUE_VALUE':84},
    '3':{'type':'RANGED_VALUE','COMPLICATION.RANGED_VALUE_VALUE':42,'COMPLICATION.TEXT':'NE · 042°'},
}


class Evaluator:
    def __init__(self):
        script=r'''
const rl = require('readline').createInterface({ input: process.stdin });
rl.on('line', line => {
  try {
    const {expression, values} = JSON.parse(line);
    const e = expression.replace(/\[([^\]]+)\]/g, (_, key) => JSON.stringify(values[key] ?? null));
    const clamp = (v, lo, hi) => Math.max(lo, Math.min(v, hi));
    const round = Math.round, floor = Math.floor;
    const textLength = s => (s ?? '').length;
    const subText = (s, start, end) => (s ?? '').substring(start, end);
    const numberFormat = (fmt, v) => {
      if (fmt.includes('%')) throw Error('Expected DecimalFormat pattern, not printf');
      return fmt.includes(',') ? Math.round(v).toLocaleString('en-US') : String(Math.round(v));
    };
    const icuText = (fmt, stamp) => {
      const date = new Date(stamp ?? values.UTC_TIMESTAMP);
      if (fmt === 'HH:mm') return date.toISOString().slice(11,16);
      return ['SUN','MON','TUE','WED','THU','FRI','SAT'][date.getUTCDay()]+' '+String(date.getUTCDate()).padStart(2,'0');
    };
    console.log(JSON.stringify({result:eval(e)}));
  } catch (error) { console.log(JSON.stringify({error:String(error)})); }
});
'''
        self.process=subprocess.Popen(['node','-e',script],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    def __call__(self,expression,values):
        self.process.stdin.write(json.dumps({'expression':expression,'values':values})+'\n')
        self.process.stdin.flush()
        response=json.loads(self.process.stdout.readline())
        if 'error' in response:
            raise ValueError(f'{expression}: {response["error"]}')
        return response.get('result')
    def close(self):
        self.process.stdin.close();self.process.wait(timeout=5);self.process.stdout.close()


class Renderer:
    def __init__(self, ambient=False, values=None, complications=None):
        self.ambient=ambient
        self.values=DEFAULTS | (values or {})
        self.complications=COMPLICATIONS if complications is None else complications
        self.evaluate=Evaluator()
        self.masks={}
    def props(self,node,values):
        props=dict(node.attrib)
        for transform in node.findall('Transform'):
            props[transform.get('target')]=self.evaluate(transform.get('value'),values)
        if self.ambient:
            for variant in node.findall("Variant[@mode='AMBIENT']"):
                props[variant.get('target')]=variant.get('value')
        return props
    def font(self,f):
        return ImageFont.truetype(str(RES/'font'/(f.get('family')+'.ttf')),float(f.get('size')))
    def content(self,font,values):
        t=font.find('Template')
        if t is None:return font.text or ''
        parameters=tuple('' if (value:=self.evaluate(p.get('expression'),values)) is None else str(value)
                         for p in t.findall('Parameter'))
        return t.text % parameters
    def render(self,node,values=None):
        values=self.values if values is None else values
        p=self.props(node,values)
        layer=Image.new('RGBA',(480,480))
        if float(p.get('alpha',255)) == 0:return layer
        tag=node.tag
        if tag=='Condition':
            expressions={e.get('name'):e.text for e in node.findall('./Expressions/Expression')}
            selected=next((c for c in node.findall('Compare') if self.evaluate(expressions[c.get('expression')],values)),node.find('Default'))
            if selected is not None:layer=self.render(selected,values)
            return layer
        if tag=='ComplicationSlot':
            payload=self.complications.get(p['slotId'],{'type':'EMPTY'})
            for child in node.findall('Complication'):
                if child.get('type')==payload['type']:
                    layer=self.render(child,values|payload)
                    break
        elif tag=='PartText':
            t=node.find('Text')
            if t is None:t=node.find('TextCircular')
            f=t.find('Font');font=self.font(f);value=self.content(f,values)
            color=f.get('color','#91F894')
            d=ImageDraw.Draw(layer)
            if t.tag=='Text':
                d.text((int(p['x'])+int(p['width'])/2,int(p['y'])+int(p['height'])/2),value,font=font,fill=color,anchor='mm')
            else:
                radius=float(t.get('width'))/2
                start,end=float(t.get('startAngle')),float(t.get('endAngle'))
                direction=1 if t.get('direction','CLOCKWISE')=='CLOCKWISE' else -1
                available=math.radians(abs(end-start))*radius
                if font.getlength(value)>available:
                    prefix=value.rstrip('…')
                    while prefix and font.getlength(prefix+'…')>available:
                        prefix=prefix[:-1]
                    value=prefix+'…' if font.getlength('…')<=available else ''
                advances=[font.getlength(char)/radius*180/math.pi for char in value]
                alignment = t.get('align', 'CENTER')
                angle = start if alignment == 'START' else (end-direction*sum(advances) if alignment == 'END' else (start+end)/2-direction*sum(advances)/2)
                for char,advance in zip(value,advances):
                    angle+=direction*advance/2
                    glyph=Image.new('RGBA',(80,80))
                    gd=ImageDraw.Draw(glyph)
                    gd.text((40,40),char,font=font,fill=color,anchor='ms')
                    rotation=-angle if direction==1 else 180-angle
                    glyph=glyph.rotate(rotation,resample=Image.Resampling.BICUBIC)
                    x=float(p['x'])+float(t.get('centerX'))+radius*math.sin(math.radians(angle))
                    y=float(p['y'])+float(t.get('centerY'))-radius*math.cos(math.radians(angle))
                    layer.alpha_composite(glyph,(round(x-40),round(y-40)))
                    angle+=direction*advance/2
        elif tag=='PartImage':
            resource=node.find('Image').get('resource')
            if resource.startswith('['):resource=self.evaluate(resource,values)
            if resource:
                image=Image.open(RES/'drawable'/(resource+'.png')).convert('RGBA')
                image=image.resize((int(p['width']),int(p['height'])),Image.Resampling.LANCZOS)
                layer.alpha_composite(image,(int(p['x']),int(p['y'])))
        elif tag=='PartDraw':
            d=ImageDraw.Draw(layer)
            for shape in node:
                s=self.props(shape,values)
                stroke=shape.find('Stroke');fill=shape.find('Fill')
                color=stroke.get('color') if stroke is not None else (fill.get('color') if fill is not None else None)
                if color is None:continue
                if len(color)==9:color='#'+color[3:]+color[1:3] # WFF ARGB -> Pillow RGBA
                thickness=max(1,round(float(stroke.get('thickness',1)))) if stroke is not None else 1
                if shape.tag=='Line':
                    d.line(tuple(float(s[k]) for k in ('startX','startY','endX','endY')),fill=color,width=thickness)
                elif shape.tag=='Ellipse':
                    b=(float(s['x']),float(s['y']),float(s['x'])+float(s['width']),float(s['y'])+float(s['height']))
                    d.ellipse(b,outline=color if stroke is not None else None,fill=color if fill is not None else None,width=thickness)
                elif shape.tag=='Arc':
                    cx,cy=float(s['centerX'])+float(p.get('x',0)),float(s['centerY'])+float(p.get('y',0));r=float(s['width'])/2
                    start,end=float(s['startAngle']),float(s['endAngle'])
                    if shape.get('direction','CLOCKWISE')=='COUNTER_CLOCKWISE':start,end=end,start
                    d.arc((cx-r,cy-r,cx+r,cy+r),start-90,end-90,fill=color,width=thickness)
                    if stroke.get('cap')=='ROUND':
                        for angle in (start,end):
                            x=cx+(r-thickness/2)*math.sin(math.radians(angle));y=cy-(r-thickness/2)*math.cos(math.radians(angle))
                            d.ellipse((x-thickness/2,y-thickness/2,x+thickness/2,y+thickness/2),fill=color)
        else:
            for child in node:
                if child.tag not in ('Transform','Variant','Localization','UserConfigurations','DefaultProviderPolicy','BoundingRoundBox'):
                    layer.alpha_composite(self.render(child,values))
        if 'tintColor' in p:
            tinted=Image.new('RGBA',layer.size,p['tintColor']);tinted.putalpha(layer.getchannel('A'));layer=tinted
        if 'angle' in p:
            center=(float(p.get('x',0))+float(p.get('width',480))/2,
                    float(p.get('y',0))+float(p.get('height',480))/2)
            layer=layer.rotate(-float(p['angle']),resample=Image.Resampling.BICUBIC,center=center)
        if 'scaleX' in p or 'scaleY' in p:
            sx,sy=float(p.get('scaleX',1)),float(p.get('scaleY',1))
            cx = float(p.get('x',0)) + float(p.get('width',480))*float(p.get('pivotX',.5))
            cy = float(p.get('y',0)) + float(p.get('height',480))*float(p.get('pivotY',.5))
            layer=layer.transform(layer.size,Image.Transform.AFFINE,
                (1/sx,0,cx-cx/sx,0,1/sy,cy-cy/sy),Image.Resampling.BICUBIC)
        if p.get('name') in ('main_time',):self.masks[p['name']]=layer.getchannel('A')
        if p.get('name')=='clock':self.masks['main_time']=layer.getchannel('A')
        if tag=='ComplicationSlot' and p['slotId']=='1':self.masks['calendar']=layer.getchannel('A')
        return layer
    def save(self,path):
        try:
            root=ET.parse(RES/'raw/watchface.xml').getroot()
            image=Image.new('RGBA',(480,480),'#020704')
            image.alpha_composite(self.render(root.find('Scene')))
            image.resize((498,498),Image.Resampling.LANCZOS).convert('RGB').save(path)
        finally:self.evaluate.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ambient',action='store_true')
    parser.add_argument('--output',default='artifacts/preview-active.png')
    args=parser.parse_args()
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Renderer(ambient=args.ambient).save(args.output)
