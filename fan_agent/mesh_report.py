"""Extract evidence from OpenFOAM logs without treating process success as acceptance."""
import math
import re


def summarize(check, mesher, zones):
    def value(pattern, source=check, cast=float):
        matches = re.findall(pattern, source, re.M)
        if not matches:
            return None
        result = cast(matches[-1].rstrip('.'))
        return result if math.isfinite(result) else None
    row = re.findall(r'^(?:fan|fan_bladeWalls)\s+(\d+)\s+(\d+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*$', mesher, re.M)
    layer = None
    if row:
        faces, target, actual, thickness, percent = row[-1]
        layer = dict(patch_faces=int(faces), target_layers=int(target), mean_layers=float(actual),
                     mean_thickness_m=float(thickness), thickness_percent_of_requested=float(percent))
    passed = bool(re.search(r'^Mesh OK\.\s*$', check, re.M)) and not re.search(r'Failed\s+\d+\s+mesh checks', check)
    count = value(r'cellZoneSet rotor now size (\d+)', zones, int)
    added = value(r'Writing (\d+) added cells to cellSet addedCells', mesher, int)
    extruded = re.findall(r'Extruding (\d+) out of (\d+) faces', mesher)
    extrusion = dict(extruded_faces=int(extruded[-1][0]), candidate_faces=int(extruded[-1][1])) if extruded else None
    return dict(extended_mesh_check_passed=passed, rotor_cells=count,
                added_layer_cells=added, face_extrusion=extrusion,
                development_gate_passed=bool(passed and count and added),
                total_cells=value(r'^\s*cells:\s*(\d+)', check, int),
                concave_cells=value(r'Concave cells .*?number of cells:\s*(\d+)', check, int),
                small_determinant_cells=value(r'Cells with small determinant .*?number of cells:\s*(\d+)', check, int),
                min_volume_m3=value(r'Min volume = ([\d.eE+-]+)'),
                max_non_orthogonality_deg=value(r'Mesh non-orthogonality Max:\s*([\d.eE+-]+)'),
                max_skewness=value(r'Max skewness = ([\d.eE+-]+)'),
                layers=layer, accepted_for_solver=False,
                note='Missing counts mean not reported, not zero. Layer mean and thickness are not coverage or y-plus validation.')
