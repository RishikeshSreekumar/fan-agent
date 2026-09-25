from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'wireframe-data.json').read_text())
im=Image.new('RGB',(1400,760),'white');draw=ImageDraw.Draw(im)
colors={17:'#60748c',18:'#9b6b1f',20:'#777777',22:'#777777',35:'#ce2332'}
for group in data:
 if group['id'] not in colors:continue
 for curve in group['curves_mm']:
  front=[(350+(x+400)*.9,390-(z-1515)*.9) for x,y,z in curve]
  side=[(790+(y+550)*.9,390-(z-1515)*.9) for x,y,z in curve]
  draw.line(front,fill=colors[group['id']],width=1)
  draw.line(side,fill=colors[group['id']],width=1)
draw.text((30,30),'FAN-01: native CAD wireframe audit (millimetres)',fill='black')
draw.text((100,70),'Front projection: native X-Z',fill='black');draw.text((840,70),'Side projection: native Y-Z; downstream to right',fill='black')
draw.text((100,710),'Red: rotor group 35. Blue: nozzle/duct group 17. Ochre: diffuser group 18. Grey: shaft/support.',fill='black')
im.save(ROOT/'geometry-audit.png')
