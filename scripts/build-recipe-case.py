"""Build one mesh level of the Phase 1 recipe case: synthetic fan, Gmsh tetrahedra, solver dictionaries."""
import hashlib
import json
import math
from pathlib import Path
import sys
import gmsh
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fan_agent.recipe import RECIPE, SYNTHETIC_FAN as FAN, mesh_sizes, rotor_zone, write_case
from fan_agent.tetra import subdivide_boundary_tets

root, level, rpm, direction = Path(sys.argv[1]).resolve(), sys.argv[2], float(sys.argv[3]), sys.argv[4]
procs = int(sys.argv[5]) if len(sys.argv) > 5 else 1
sizes = mesh_sizes(level)
write_case(root, rpm, direction, procs=procs)  # validates rpm/direction before meshing
cx, cy, cz = FAN["center_m"]
lx, ly, lz = FAN["room_m"]
gmsh.initialize()
try:
    hub = gmsh.model.occ.addCylinder(cx, cy, cz - FAN["hub_height_m"] / 2, 0, 0, FAN["hub_height_m"], FAN["hub_radius_m"])
    blades = []
    for index in range(FAN["blades"]):
        blade = gmsh.model.occ.addBox(cx + FAN["blade_inner_m"], cy - FAN["blade_chord_m"] / 2, cz - FAN["blade_thickness_m"] / 2,
                                      FAN["blade_length_m"], FAN["blade_chord_m"], FAN["blade_thickness_m"])
        gmsh.model.occ.rotate([(3, blade)], cx, cy, cz, 1, 0, 0, math.radians(FAN["pitch_deg"]))
        gmsh.model.occ.rotate([(3, blade)], cx, cy, 0, 0, 0, 1, 2 * math.pi * index / FAN["blades"])
        blades.append((3, blade))
    fan, _ = gmsh.model.occ.fuse([(3, hub)], blades)
    room = gmsh.model.occ.addBox(cx - lx / 2, cy - ly / 2, 0, lx, ly, lz)
    fluid, _ = gmsh.model.occ.cut([(3, room)], fan)
    gmsh.model.occ.synchronize()
    groups = {"floor": [], "ceiling": [], "roomWalls": [], "fan": []}
    for _, tag in gmsh.model.getBoundary(fluid, oriented=False):
        x, y, z = gmsh.model.occ.getCenterOfMass(2, tag)
        name = ("floor" if abs(z) < 1e-6 else "ceiling" if abs(z - lz) < 1e-6 else
                "roomWalls" if abs(abs(x - cx) - lx / 2) < 1e-6 or abs(abs(y - cy) - ly / 2) < 1e-6 else "fan")
        groups[name].append(tag)
    for name, tags in groups.items():
        if not tags:
            raise ValueError("Missing CAD patch: " + name)
        gmsh.model.addPhysicalGroup(2, tags, name=name)
    gmsh.model.addPhysicalGroup(3, [tag for _, tag in fluid], name="fluid")
    distance = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(distance, "FacesList", groups["fan"])
    gmsh.model.mesh.field.setNumber(distance, "Sampling", 100)
    threshold = gmsh.model.mesh.field.add("Threshold")
    for key, value in {"InField": distance, "SizeMin": sizes["near_fan"], "SizeMax": sizes["bulk"],
                       "DistMin": sizes["grade_start"], "DistMax": sizes["grade_end"]}.items():
        gmsh.model.mesh.field.setNumber(threshold, key, value)
    gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
    gmsh.option.setNumber("Mesh.MeshSizeMin", sizes["minimum"])
    gmsh.option.setNumber("Mesh.MeshSizeMax", sizes["bulk"])
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 24)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.Binary", 0)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("")
    subdivided = 0  # full-rank stencils at boundary corners; see scripts/build-cad-volume.py
    for _, volume in fluid:
        element_tags, connectivity = gmsh.model.mesh.getElementsByType(4, volume)
        tets = [list(map(int, connectivity[i:i + 4])) for i in range(0, len(connectivity), 4)]
        tags, coords, _ = gmsh.model.mesh.getNodes()
        nodes = {int(tag): list(coords[3 * i:3 * i + 3]) for i, tag in enumerate(tags)}
        updated_nodes, updated_elements, split = subdivide_boundary_tets(nodes, dict(zip(map(int, element_tags), tets)))
        if split:
            new_nodes = [tag for tag in updated_nodes if tag not in nodes]
            volume_nodes, volume_coords, _ = gmsh.model.mesh.getNodes(3, volume)
            gmsh.model.mesh.clear([(3, volume)])
            gmsh.model.mesh.addNodes(3, volume, list(volume_nodes) + new_nodes,
                                     list(volume_coords) + [v for tag in new_nodes for v in updated_nodes[tag]])
            gmsh.model.mesh.addElementsByType(volume, 4, list(updated_elements), [n for t in updated_elements.values() for n in t])
        subdivided += split
    gmsh.write(str(root / "volume.msh"))
    fluid_volume = sum(gmsh.model.occ.getMass(3, tag) for _, tag in fluid)
    (root / "manifest.json").write_text(json.dumps({
        "classification": "phase1_recipe_mesh_study", "recipe": RECIPE["id"], "level": level,
        "refinement_scale": sizes["near_fan"] / .012, "mesh_sizes_m": sizes, "mesher": "Gmsh " + gmsh.__version__,
        "geometry": "synthetic three pitched rectangular blades and hub", "fan": FAN, "rotor_zone": rotor_zone(),
        "rpm": rpm, "direction": direction, "fluid_volume_m3": fluid_volume, "subdivided_boundary_tets": subdivided,
        "volume_msh_sha256": hashlib.sha256((root / "volume.msh").read_bytes()).hexdigest(),
        "accepted_performance": False}, indent=2))
finally:
    gmsh.finalize()
