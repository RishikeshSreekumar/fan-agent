"""Prepare a metre-based rotor and audit its tessellated closed surface."""
from pathlib import Path
import gmsh,json,math,hashlib,collections,sys
ROOT=Path(__file__).resolve().parent
source=ROOT/'recovered-35-0.001.brep'
gmsh.initialize()
try:
 gmsh.model.occ.importShapes(str(source));gmsh.model.occ.synchronize()
 if len(gmsh.model.getEntities(3))!=1:raise ValueError('Expected one recovered rotor solid.')
 matrix=[0,.001,0,.460, 0,0,.001,-1.515, .001,0,0,.400, 0,0,0,1]
 gmsh.model.occ.affineTransform(gmsh.model.getEntities(3),matrix);gmsh.model.occ.synchronize()
 gmsh.write(str(ROOT/'rotor-metres.brep'))
 gmsh.option.setNumber('Mesh.MeshSizeMin',.00025);gmsh.option.setNumber('Mesh.MeshSizeMax',.003)
 curvature=0 if '--constant-size' in sys.argv else 48
 gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',curvature)
 gmsh.option.setNumber('Mesh.Algorithm',6)
 gmsh.model.mesh.generate(2)
 tags,coords,_=gmsh.model.mesh.getNodes();points={int(t):tuple(float(v) for v in coords[3*i:3*i+3]) for i,t in enumerate(tags)}
 types,element_tags,node_tags=gmsh.model.mesh.getElements(2)
 triangles=[]
 for kind,connectivity in zip(types,node_tags):
  if kind!=2:raise ValueError('Expected triangle surface elements only.')
  triangles.extend(tuple(int(v) for v in connectivity[i:i+3]) for i in range(0,len(connectivity),3))
 edges=collections.Counter(tuple(sorted((a,b))) for t in triangles for a,b in zip(t,(t[1],t[2],t[0])))
 if any(v!=2 for v in edges.values()):raise ValueError('Surface mesh is not closed/manifold.')
 def signed_volume(t):
  a,b,c=(points[i] for i in t)
  return (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
 signed=sum(map(signed_volume,triangles));volume=sum(gmsh.model.occ.getMass(d,t) for d,t in gmsh.model.getEntities(3))
 if abs(abs(signed)-volume)/volume>.005:raise ValueError('Surface and CAD volume disagree.')
 gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(ROOT/'rotor-metres.stl'))
 report={'curvature_sizing':curvature,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'transform_from_native_mm':matrix,'frame':'x downstream (native Y); y up (native Z); z native X. Origin (-400,-460,1515) mm at nozzle/straight-duct transition; not asserted to be LDA origin.','rotation_axis':[1,0,0],'counts':{'faces':len(gmsh.model.getEntities(2)),'triangles':len(triangles),'nodes':len(points)},'cad_volume_m3':volume,'surface_signed_volume_m3':signed,'surface_volume_relative_error':abs(abs(signed)-volume)/volume,'surface_closed_manifold':True,'maximum_sampled_radius_m':max(math.hypot(p[1],p[2]) for p in points.values()),'nominal_radial_gap_m':.0025,'bounds_from_mesh_m':[min(p[i] for p in points.values()) for i in range(3)]+[max(p[i] for p in points.values()) for i in range(3)],'status':'rotor_surface_prepared_not_volume_mesh_or_solver_validation'}
 (ROOT/'rotor-preparation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:gmsh.finalize()
