"""CAD-subtracted tetrahedral baseline; same synthetic fan, no prism-layer claim."""
import hashlib
import json
import math
from pathlib import Path
import sys
import gmsh
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fan_agent.tetra import subdivide_boundary_tets

root = Path(sys.argv[1]).resolve()
gmsh.initialize()
try:
    hub = gmsh.model.occ.addCylinder(0, 0, 2.36, 0, 0, .08, .11)
    blades = []
    for angle in (0, 120, 240):
        blade = gmsh.model.occ.addBox(.07, -.065, 2.38, .5, .13, .04)
        gmsh.model.occ.rotate([(3, blade)], 0, 0, 2.4, 1, 0, 0, math.radians(12))
        gmsh.model.occ.rotate([(3, blade)], 0, 0, 0, 0, 0, 1, math.radians(angle))
        blades.append((3, blade))
    fan, _ = gmsh.model.occ.fuse([(3, hub)], blades)
    room = gmsh.model.occ.addBox(-2, -2, 0, 4, 4, 3)
    fluid, _ = gmsh.model.occ.cut([(3, room)], fan)
    gmsh.model.occ.synchronize()
    gmsh.write(str(root/'fluid.brep'))
    groups = {'floor':[], 'ceiling':[], 'roomWalls':[], 'fan':[]}
    for _, tag in gmsh.model.getBoundary(fluid, oriented=False):
        x,y,z = gmsh.model.occ.getCenterOfMass(2, tag)
        name = 'floor' if abs(z)<1e-6 else 'ceiling' if abs(z-3)<1e-6 else 'roomWalls' if abs(abs(x)-2)<1e-6 or abs(abs(y)-2)<1e-6 else 'fan'
        groups[name].append(tag)
    for name,tags in groups.items():
        if not tags: raise ValueError('Missing CAD patch: '+name)
        gmsh.model.addPhysicalGroup(2, tags, name=name)
    gmsh.model.addPhysicalGroup(3, [tag for _,tag in fluid], name='fluid')
    distance = gmsh.model.mesh.field.add('Distance')
    gmsh.model.mesh.field.setNumbers(distance, 'FacesList', groups['fan'])
    gmsh.model.mesh.field.setNumber(distance, 'Sampling', 100)
    threshold = gmsh.model.mesh.field.add('Threshold')
    for key,value in {'InField':distance,'SizeMin':.012,'SizeMax':.20,'DistMin':.025,'DistMax':.45}.items():
        gmsh.model.mesh.field.setNumber(threshold,key,value)
    gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
    gmsh.option.setNumber('Mesh.MeshSizeMin', .006)
    gmsh.option.setNumber('Mesh.MeshSizeMax', .20)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 24)
    gmsh.option.setNumber('Mesh.MshFileVersion', 2.2)
    gmsh.option.setNumber('Mesh.Binary', 0)
    gmsh.option.setNumber('Mesh.Algorithm3D', 1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize('')
    # Boundary-corner tets with two or more boundary faces have too few
    # neighbouring cells for a full-rank finite-volume stencil. Subdivide
    # those cells at their centroid, preserving all external triangles.
    subdivided = 0
    for _,volume in fluid:
        element_tags, connectivity = gmsh.model.mesh.getElementsByType(4, volume)
        tets = [list(map(int,connectivity[i:i+4])) for i in range(0,len(connectivity),4)]
        tags, coords, _ = gmsh.model.mesh.getNodes()
        nodes = {int(tag):list(coords[3*i:3*i+3]) for i,tag in enumerate(tags)}
        updated_nodes,updated_elements,split_count = subdivide_boundary_tets(nodes,dict(zip(map(int,element_tags),tets)))
        if split_count:
            new_nodes = [tag for tag in updated_nodes if tag not in nodes]
            new_coords = [v for tag in new_nodes for v in updated_nodes[tag]]
            volume_nodes,volume_coords,_ = gmsh.model.mesh.getNodes(3,volume)
            gmsh.model.mesh.clear([(3,volume)])
            gmsh.model.mesh.addNodes(3,volume,list(volume_nodes)+new_nodes,list(volume_coords)+new_coords)
            gmsh.model.mesh.addElementsByType(volume,4,list(updated_elements),[n for t in updated_elements.values() for n in t])
        subdivided += split_count
    gmsh.write(str(root/'volume.msh'))
    manifest = json.loads((root/'manifest.json').read_text())
    manifest.update(mesher='Gmsh '+gmsh.__version__, method='CAD subtraction / tetrahedral',
                    requested_wall_layers=0, layer_patch=None,
                    near_wall_target_m=.012, bulk_target_m=.20, subdivided_boundary_tets=subdivided,
                    limitations='Near-wall refinement only, no prism layers. Wall treatment, y-plus, grid sensitivity and performance accuracy unqualified.',
                    cad_sha256=hashlib.sha256((root/'fluid.brep').read_bytes()).hexdigest())
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2))
finally:
    gmsh.finalize()
