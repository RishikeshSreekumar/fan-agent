from pathlib import Path
import gmsh,json,math
ROOT=Path(__file__).resolve().parent
groups=json.loads((ROOT/'surface-components.json').read_text())
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.model.occ.importShapes(str(ROOT/'healed-assembly.brep'));gmsh.model.occ.synchronize()
 result=[]
 for group in groups:
  curves=[]
  edges=sorted({abs(e) for face in group['faces'] for d,e in gmsh.model.getBoundary([(2,face)],oriented=False)})
  for edge in edges:
   lo,hi=gmsh.model.getParametrizationBounds(1,edge);lo=float(lo[0]);hi=float(hi[0])
   values=gmsh.model.getValue(1,edge,[lo+(hi-lo)*i/24 for i in range(25)])
   curves.append([list(values[i:i+3]) for i in range(0,len(values),3)])
  points=[p for curve in curves for p in curve]
  result.append({'id':group['id'],'curves_mm':curves,'sampled_bounds_mm':[min(p[i] for p in points) for i in range(3)]+[max(p[i] for p in points) for i in range(3)]})
 (ROOT/'wireframe-data.json').write_text(json.dumps(result))
 for r in result:print(r['id'],r['sampled_bounds_mm'])
finally:gmsh.finalize()
