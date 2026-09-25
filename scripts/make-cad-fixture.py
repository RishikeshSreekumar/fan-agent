"""Synthetic metre-scale box with a curved hole; not a fan model."""
import gmsh
from pathlib import Path
gmsh.initialize()
try:
    box = gmsh.model.occ.addBox(0, 0, 0, 100, 80, 20)
    hole = gmsh.model.occ.addCylinder(50, 40, -1, 0, 0, 22, 10)
    gmsh.model.occ.cut([(3, box)], [(3, hole)])
    gmsh.model.occ.synchronize()
    gmsh.write(str(Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "cad-mm.step"))
finally:
    gmsh.finalize()
