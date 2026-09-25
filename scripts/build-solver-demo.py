"""Fixed engineering development case; no designer inputs or accepted results."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
(root/'0').mkdir(exist_ok=True)
def write(folder,name,body,kind='dictionary'):
    (root/folder/name).write_text(f'FoamFile {{ version 2.0; format ascii; class {kind}; object {name}; }}\n'+body)
walls=('fan','floor','ceiling','roomWalls')
(root/'system/airflowPlane').write_text(Path(__file__).with_name('airflowPlane').read_text())
write('constant','transportProperties','transportModel Newtonian; nu [0 2 -1 0 0 0 0] 1.5e-5;')
write('constant','turbulenceProperties','simulationType RAS; RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }')
write('constant','MRFProperties','rotorMRF { cellZone rotor; active yes; nonRotatingPatches (floor ceiling roomWalls); origin (0 0 2.4); axis (0 0 1); omega -29.3215314335; }')
for name,dimensions,value,bc in (
 ('U','0 1 -1 0 0 0 0','(0 0 0)','noSlip'),
 ('p','0 2 -2 0 0 0 0','0','zeroGradient'),
 ('k','0 2 -2 0 0 0 0','0.01','kqRWallFunction'),
 ('omega','0 0 -1 0 0 0 0','10','omegaWallFunction'),
 ('nut','0 2 -1 0 0 0 0','0','nutkWallFunction')):
    boundary=' '.join(f'{w} {{ type {bc};'+(f' value uniform {value};' if bc not in ('noSlip','zeroGradient') else '')+' }' for w in walls)
    write('0',name,f'dimensions [{dimensions}]; internalField uniform {value}; boundaryField {{ {boundary} }}','volVectorField' if name=='U' else 'volScalarField')
write('system','fvSchemes','''
ddtSchemes { default steadyState; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss upwind; div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
''')
write('system','fvSolution','''
solvers {
 p {solver GAMG; tolerance 1e-8; relTol 0.05; smoother GaussSeidel;}
 "(U|k|omega)" {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0.1;}
}
SIMPLE { nNonOrthogonalCorrectors 1; pRefCell 0; pRefValue 0; }
relaxationFactors { fields {p 0.2;} equations {U 0.4; k 0.4; omega 0.4;} }
''')
write('system','controlDict','''
application simpleFoam; startFrom startTime; startTime 0; stopAt endTime;
endTime 300; deltaT 1; writeControl timeStep; writeInterval 100; writeFormat ascii;
writePrecision 10; purgeWrite 0; runTimeModifiable false;
functions {
 fanLoads { type forces; libs ("libforces.so"); patches (fan); rho rhoInf; rhoInf 1.2;
 CofR (0 0 2.4); log true; writeControl timeStep; writeInterval 1; }
 wallYPlus {type yPlus; libs ("libfieldFunctionObjects.so"); executeControl timeStep; executeInterval 50; writeControl timeStep; writeInterval 50;}
}
''')
