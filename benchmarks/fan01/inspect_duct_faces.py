from pathlib import Path
import gmsh,json,math
ROOT=Path(__file__).resolve().parent
groups=json.loads((ROOT/'surface-components.json').read_text())
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.model.occ.importShapes(str(ROOT/'healed-assembly.brep'));gmsh.model.occ.synchronize();result=[]
 for gid in (17,18,19):
  g=next(g for g in groups if g['id']==gid)
  for tag in g['faces']:
   area=gmsh.model.occ.getMass(2,tag)
   if area<10000:continue
   lo,hi=gmsh.model.getParametrizationBounds(2,tag)
   uv=[v for i in range(11) for j in range(11) for v in (lo[0]+(hi[0]-lo[0])*i/10,lo[1]+(hi[1]-lo[1])*j/10)]
   coords=gmsh.model.getValue(2,tag,uv);points=[list(coords[i:i+3]) for i in range(0,len(coords),3)]
   rs=[math.hypot(p[0]+400,p[2]-1515) for p in points];ys=[p[1] for p in points]
   record={'group':gid,'face':tag,'area_mm2':area,'axial_Y_mm':[min(ys),max(ys)],'radius_mm':[min(rs),max(rs)],'points_mm':points}
   result.append(record);print({k:v for k,v in record.items() if k!='points_mm'})
 (ROOT/'duct-face-audit.json').write_text(json.dumps(result,indent=2))
finally:gmsh.finalize()
