"""Create a fixed synthetic rotor for meshing development, not aerodynamic design."""
import json
import math
from pathlib import Path
import sys
import gmsh

root = Path(sys.argv[1]).resolve()
profile = sys.argv[2] if len(sys.argv) > 2 else 'medial'
if profile not in {'medial', 'motion', 'motion-unmerged'}:
    raise ValueError('Unsupported diagnostic mesh profile.')
surface = root / 'constant' / 'triSurface'
surface.mkdir(parents=True, exist_ok=True)
(root / 'system').mkdir(exist_ok=True)
gmsh.initialize()
try:
    hub = gmsh.model.occ.addCylinder(0, 0, 2.36, 0, 0, .08, .11)
    blades = []
    for angle in (0, 120, 240):
        blade = gmsh.model.occ.addBox(.07, -.065, 2.38, .5, .13, .04)
        gmsh.model.occ.rotate([(3, blade)], 0, 0, 2.4, 1, 0, 0, math.radians(12))
        gmsh.model.occ.rotate([(3, blade)], 0, 0, 0, 0, 0, 1, math.radians(angle))
        blades.append((3, blade))
    gmsh.model.occ.fuse([(3, hub)], blades)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMin', .002)
    gmsh.option.setNumber('Mesh.MeshSizeMax', .008)
    gmsh.model.mesh.generate(2)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    nodes = {int(tag):coords[3*i:3*i+3] for i,tag in enumerate(tags)}
    groups = {'bladeWalls':[], 'fanEdges':[]}
    for _, tag in gmsh.model.getEntities(2):
        cx, cy, _ = gmsh.model.occ.getCenterOfMass(2, tag)
        _, connectivity = gmsh.model.mesh.getElementsByType(2, tag)
        for i in range(0, len(connectivity), 3):
            a,b,c = [nodes[int(n)] for n in connectivity[i:i+3]]
            u,v = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
            normal = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            length = math.sqrt(sum(n*n for n in normal))
            normal = [n/length for n in normal]
            broad_blade = cx*cx+cy*cy > .15**2 and abs(normal[2]) > .9
            group = 'bladeWalls' if broad_blade else 'fanEdges'
            groups[group].append('facet normal '+' '.join(map(str,normal))+'\nouter loop\n'+''.join('vertex '+' '.join(map(str,p))+'\n' for p in (a,b,c))+'endloop\nendfacet\n')
    (surface/'fan.stl').write_text(''.join('solid '+name+'\n'+''.join(facets)+'endsolid '+name+'\n' for name,facets in groups.items()))
finally:
    gmsh.finalize()

def write(name, body):
    (root/'system'/name).write_text('FoamFile { version 2.0; format ascii; class dictionary; object '+name+'; }\n'+body)

write('controlDict', 'application snappyHexMesh; startFrom startTime; startTime 0; stopAt endTime; endTime 1; deltaT 1; writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 8; runTimeModifiable false;')
write('fvSchemes', 'ddtSchemes { default steadyState; } gradSchemes { default Gauss linear; } divSchemes { default none; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; }')
write('fvSolution', 'solvers { "cellDisplacement.*" { solver GAMG; tolerance 1e-8; relTol 0; smoother GaussSeidel; minIter 2; } }')
write('meshQualityDict', '#includeEtc "caseDicts/mesh/generation/meshQualityDict.cfg"')
write('surfaceFeatureExtractDict', 'fan.stl { extractionMethod extractFromSurface; extractFromSurfaceCoeffs { includedAngle 150; } writeObj yes; }')
write('blockMeshDict', '''
scale 1;
vertices ((-2 -2 0)(2 -2 0)(2 2 0)(-2 2 0)(-2 -2 3)(2 -2 3)(2 2 3)(-2 2 3));
blocks (hex (0 1 2 3 4 5 6 7) (32 32 24) simpleGrading (1 1 1));
edges ();
boundary (
floor {type wall; faces ((0 3 2 1));}
ceiling {type wall; faces ((4 5 6 7));}
roomWalls {type wall; faces ((0 1 5 4)(1 2 6 5)(2 3 7 6)(3 0 4 7));}
);
''')
write('snappyHexMeshDict', '''
#includeEtc "caseDicts/mesh/generation/snappyHexMeshDict.cfg"
castellatedMesh true;
snap true;
addLayers true;
geometry {
 fan.stl {type triSurfaceMesh; name fan;}
 rotor {type searchableCylinder; point1 (0 0 2.2); point2 (0 0 2.6); radius 0.68;}
}
castellatedMeshControls {
 maxLocalCells 500000; maxGlobalCells 500000;
 minRefinementCells 0; nCellsBetweenLevels 5;
 features ({file "fan.eMesh"; level 4;});
 refinementSurfaces {fan {level (4 4); patchInfo {type wall;}}}
 refinementRegions {rotor {mode inside; levels ((1e15 2));}}
 locationInMesh (1.7 1.7 0.3);
}
snapControls {
 implicitFeatureSnap false; explicitFeatureSnap true; nFeatureSnapIter 20;
 nSmoothPatch 5; nSmoothInternal 10; tolerance 1.0; nSolveIter 100; nRelaxIter 8;
}
addLayersControls {
 layers {fan_bladeWalls {nSurfaceLayers 3;}}
 relativeSizes false; expansionRatio 1.2; firstLayerThickness 0.001; minThickness 0.0018;
 featureAngle 60; nGrow 0; nBufferCellsNoExtrude 1;
 nSmoothSurfaceNormals 0; nSmoothNormals 0; nSmoothThickness 0;
 nLayerIter 50; nRelaxedIter 50;
}
writeFlags (layerSets layerFields);
meshQualityControls {minDeterminant 0.01; minFaceFlatness 0.8;}
mergeTolerance 1e-6;
''')
if profile != 'medial':
    dictionary = root/'system/snappyHexMeshDict'
    content = dictionary.read_text().replace('addLayersControls {', 'addLayersControls {\n meshShrinker displacementMotionSolver;\n solver displacementLaplacian;\n displacementLaplacianCoeffs { diffusivity quadratic inverseDistance (fan_bladeWalls); }')
    if profile == 'motion-unmerged':
        content += '\nmergePatchFaces false;\n'
    dictionary.write_text(content)
write('topoSetDict', '''
actions (
{name rotorCells; type cellSet; action new; source cylinderToCell;
 sourceInfo {p1 (0 0 2.2); p2 (0 0 2.6); radius 0.68;}}
{name rotor; type cellZoneSet; action new; source setToCellZone; sourceInfo {set rotorCells;}}
);
''')
(root/'manifest.json').write_text(json.dumps({
 'classification':'experimental_mesh_only', 'profile':profile, 'geometry':'synthetic three pitched rectangular blades and hub',
 'units':'m', 'room_m':[4,4,3], 'rotor_center_m':[0,0,2.4],
 'zone_radius_m':.68, 'zone_z_m':[2.2,2.6], 'requested_wall_layers':3, 'layer_patch':'fan_bladeWalls',
 'accepted_for_solver':False, 'limitations':'Layer coverage and y-plus are unqualified. No mesh independence study. Cell-centre cylinder selection is approximate.'}, indent=2))
