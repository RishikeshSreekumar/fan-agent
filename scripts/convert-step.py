"""Run only with the WSL system Python and packaged Gmsh."""
import json
import math
from pathlib import Path
import sys
import gmsh

source, target, metadata = map(Path, sys.argv[1:4])
gmsh.initialize()
try:
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setString("Geometry.OCCTargetUnit", "M")
    gmsh.model.occ.importShapes(str(source), highestDimOnly=False)
    gmsh.model.occ.synchronize()
    solids = gmsh.model.getEntities(3)
    if not solids:
        raise ValueError("STEP must contain solid geometry; surface-only CAD needs repair.")
    bounds = gmsh.model.getBoundingBox(-1, -1)
    span = max(bounds[i+3]-bounds[i] for i in range(3))
    if not math.isfinite(span) or not 0.001 <= span <= 20:
        raise ValueError("CAD dimensions fall outside the supported 1 mm–20 m span.")
    gmsh.option.setNumber("Mesh.MeshSizeMin", span/500)
    gmsh.option.setNumber("Mesh.MeshSizeMax", span/60)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 24)
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.model.mesh.generate(2)
    gmsh.write(str(target))
    metadata.write_text(json.dumps({"engine": "Gmsh", "version": gmsh.__version__,
        "source_format": "STEP", "output_units": "m", "solid_count": len(solids),
        "bounds_m": bounds, "min_size_m": span/500, "max_size_m": span/60,
        "curvature_elements_per_2pi": 24,
        "qualification": "Draft tessellation settings; not a qualified CFD mesh."}))
finally:
    gmsh.finalize()
