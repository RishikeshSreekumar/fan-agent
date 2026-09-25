from pathlib import Path
import gmsh,json,sys,collections
ROOT=Path(__file__).resolve().parent
groups=json.loads((ROOT/'surface-components.json').read_text())
selected=[int(v) for v in sys.argv[1].split(',')];tol=float(sys.argv[2])
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.model.occ.importShapes(str(ROOT/'healed-assembly.brep'));gmsh.model.occ.synchronize()
 keep={t for g in groups if g['id'] in selected for t in g['faces']}
 gmsh.model.occ.remove([(d,t) for d,t in gmsh.model.getEntities(2) if t not in keep],recursive=True)
 gmsh.model.occ.synchronize()
 gmsh.model.occ.healShapes([],tolerance=tol,fixDegenerated=True,fixSmallEdges=True,fixSmallFaces=True,sewFaces=True,makeSolids=True)
 gmsh.model.occ.synchronize()
 report={'groups':selected,'tolerance_mm':tol,'counts':{str(d):len(gmsh.model.getEntities(d)) for d in range(4)},'volumes':[{'tag':t,'volume_mm3':gmsh.model.occ.getMass(d,t),'bounds_mm':gmsh.model.getBoundingBox(d,t)} for d,t in gmsh.model.getEntities(3)]}
 edges=collections.Counter(abs(t) for face in gmsh.model.getEntities(2) for d,t in gmsh.model.getBoundary([face],oriented=False))
 report['edge_incidence']=dict(collections.Counter(edges.values()))
 name='recovered-'+'-'.join(map(str,selected))+'-'+str(tol)
 (ROOT/(name+'.json')).write_text(json.dumps(report,indent=2));gmsh.write(str(ROOT/(name+'.brep')))
 print(json.dumps(report,indent=2))
finally:gmsh.finalize()
