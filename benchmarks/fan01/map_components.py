from pathlib import Path
import gmsh,json,collections
ROOT=Path(__file__).resolve().parent
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.model.occ.importShapes(str(ROOT/'healed-assembly.brep'));gmsh.model.occ.synchronize()
 faces=[t for d,t in gmsh.model.getEntities(2)];edges=collections.defaultdict(list);byface={}
 for t in faces:
  byface[t]=[abs(e) for d,e in gmsh.model.getBoundary([(2,t)],oriented=False)]
  for e in byface[t]:edges[e].append(t)
 unseen=set(faces);groups=[]
 while unseen:
  stack=[min(unseen)];group=[];unseen.remove(stack[0])
  while stack:
   t=stack.pop();group.append(t)
   for e in byface[t]:
    for n in edges[e]:
     if n in unseen:unseen.remove(n);stack.append(n)
  counts=collections.Counter(e for t in group for e in byface[t]);boxes=[gmsh.model.getBoundingBox(2,t) for t in group]
  groups.append({'id':len(groups),'face_count':len(group),'faces':sorted(group),'bounds_mm':[min(b[i] for b in boxes) for i in range(3)]+[max(b[i] for b in boxes) for i in range(3,6)],'area_mm2':sum(gmsh.model.occ.getMass(2,t) for t in group),'edge_incidence_histogram':dict(collections.Counter(counts.values()))})
 (ROOT/'surface-components.json').write_text(json.dumps(groups,indent=2))
 print('COMPONENTS',len(groups))
 for g in sorted(groups,key=lambda g:g['area_mm2'],reverse=True)[:60]:print({k:v for k,v in g.items() if k!='faces'})
finally:gmsh.finalize()
