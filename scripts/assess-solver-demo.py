"""Produce explicitly provisional metrics from the saved development run."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from fan_agent.solver_results import torque_summary,residuals,convergence_assessment,iteration_diagnostics
from fan_agent.cell_slice import slice_case
root=Path(sys.argv[1])
times=sorted(int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit() and int(p.name)>0 and (p/'U').exists())
planes={str(time):slice_case(root,time)[0] for time in times}
moments=sorted((root/'postProcessing/fanLoads').glob('*/moment.dat'),key=lambda p:float(p.parent.name))
torque=torque_summary('\n'.join(p.read_text() for p in moments))
log=(root/'log.simpleFoam').read_text()
final_residuals=residuals(log)
report={'case':str(root),'classification':'provisional_engineering_run','accepted_performance':False,
        'mesh':'168591-cell CAD tetrahedral baseline','rpm':280,'model':'steady MRF / kOmegaSST',
        'numerics':'First-order bounded upwind development settings',
        'execution_completed':log.rstrip().endswith('End'), 'final_initial_residuals':final_residuals,
        'convergence':convergence_assessment(final_residuals,torque,planes),
        'diagnostics':iteration_diagnostics(log),'torque':torque,'plane_height_m':1.2,'planes':planes,
        'limitations':['Synthetic geometry, not company CAD.','No mesh-sensitivity or experimental validation.',
                       'Wall y-plus is broad; wall treatment is unqualified.','Completion is not convergence.']}
(root/'solver-assessment.json').write_text(json.dumps(report,indent=2))
target=Path(__file__).resolve().parent.parent/'docs/solver-assessment.json'
target.write_text(json.dumps(report,indent=2))
_,polygons=slice_case(root,times[-1])
history=[list(map(float,line.split())) for p in moments for line in p.read_text().splitlines() if line.strip() and not line.startswith('#')]
(target.parent/'solver-plot-data.json').write_text(json.dumps({'iteration':times[-1], 'polygons':polygons,'torque_history':[[row[0],row[3]] for row in history]}))
print(json.dumps(report,indent=2))
