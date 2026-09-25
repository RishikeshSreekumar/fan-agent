"""Sew the source IGES at its stated millimetre tolerance; preserve originals."""
from pathlib import Path
import gmsh,json,time
ROOT=Path(__file__).resolve().parent
start=time.monotonic()
gmsh.initialize()
try:
 gmsh.model.occ.importShapes(str(ROOT/'extracted/cad_model/cad_model.igs'))
 gmsh.model.occ.synchronize()
 gmsh.model.occ.healShapes([],tolerance=1e-5,fixDegenerated=True,fixSmallEdges=True,fixSmallFaces=True,sewFaces=True,makeSolids=True)
 gmsh.model.occ.synchronize()
 volumes=[{'tag':t,'volume_mm3':gmsh.model.occ.getMass(d,t),'center_mm':gmsh.model.occ.getCenterOfMass(d,t),'bounds_mm':gmsh.model.getBoundingBox(d,t),'faces':len(gmsh.model.getBoundary([(d,t)],oriented=False))} for d,t in gmsh.model.getEntities(3)]
 report={'source':'extracted/cad_model/cad_model.igs','tolerance_mm':1e-5,'elapsed_s':time.monotonic()-start,'counts':{str(d):len(gmsh.model.getEntities(d)) for d in range(4)},'volumes':volumes}
 gmsh.write(str(ROOT/'healed-assembly.brep'))
 (ROOT/'component-audit.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
finally:gmsh.finalize()
