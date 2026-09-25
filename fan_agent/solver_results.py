"""Strict adapters for this development solver's recorded output formats."""
import math
import re
from .analytics import plane_metrics, load_metrics


def vtk_plane(text):
    if 'ASCII' not in text.splitlines()[:4] or 'DATASET POLYDATA' not in text:
        raise ValueError('Expected ASCII VTK POLYDATA.')
    tokens=text.split()
    i=tokens.index('POINTS'); n=int(tokens[i+1]); start=i+3
    coordinates=list(map(float,tokens[start:start+3*n]))
    points=[coordinates[j:j+3] for j in range(0,len(coordinates),3)]
    if len(points)!=n or any(len(p)!=3 or not all(math.isfinite(v) for v in p) or abs(p[2]-1.2)>1e-6 for p in points):
        raise ValueError(f'Invalid coordinates or wrong measurement plane: points={len(points)}/{n}, z range={min(p[2] for p in points)}..{max(p[2] for p in points)}.')
    i=tokens.index('POLYGONS'); count=int(tokens[i+1]); total=int(tokens[i+2]); cursor=i+3
    faces=[]
    for _ in range(count):
        size=int(tokens[cursor]); cursor+=1
        face=list(map(int,tokens[cursor:cursor+size])); cursor+=size
        if size<3 or len(face)!=size or min(face)<0 or max(face)>=n:
            raise ValueError('Invalid polygon connectivity.')
        faces.append(face)
    if cursor-(i+3)!=total: raise ValueError('Invalid polygon length.')
    i=tokens.index('CELL_DATA',cursor)
    if int(tokens[i+1])!=count: raise ValueError('Cell data count mismatch.')
    j=tokens.index('U',i)
    if tokens[j+1:j+3]!=['3',str(count)]: raise ValueError('Velocity must be a three-component cell field.')
    velocities=list(map(float,tokens[j+4:j+4+3*count]))
    if len(velocities)!=3*count or not all(math.isfinite(v) for v in velocities): raise ValueError('Truncated or nonfinite velocity field.')
    samples=[]; zero_area=0
    for index,face in enumerate(faces):
        vertices=[points[k] for k in face]
        a=vertices[0]
        area=abs(math.fsum((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1]) for b,c in zip(vertices[1:],vertices[2:])))/2
        if area==0:
            zero_area+=1
            continue
        samples.append({'area_m2':area,'velocity_ms':velocities[3*index:3*index+3]})
    metrics=plane_metrics(samples)
    metrics['zero_area_tangent_polygons']=zero_area
    if not math.isclose(metrics['plane_area_m2'],16,rel_tol=1e-5):
        raise ValueError(f"Sampled area {metrics['plane_area_m2']} does not cover the 4 m by 4 m plane.")
    return metrics


def torque_summary(text, window=50):
    rows=[list(map(float,line.split())) for line in text.splitlines() if line.strip() and not line.startswith('#')]
    if len(rows)<window or any(len(row)!=10 or not all(math.isfinite(v) for v in row) for row in rows):
        raise ValueError('Incomplete or invalid moment history.')
    tail=rows[-window:]; torque=[row[3] for row in tail]
    mean=sum(torque)/len(torque)
    spread=(max(torque)-min(torque))/max(abs(mean),1e-12)
    long_drift=None
    if len(rows)>=500:
        recent=sum(row[3] for row in rows[-250:])/250
        previous=sum(row[3] for row in rows[-500:-250])/250
        long_drift={'window_samples':250,'previous_mean_nm':previous,'recent_mean_nm':recent,
                    'relative_change':abs(recent-previous)/max(abs(recent),1e-12)}
    return {'long_window_drift':long_drift,'last_iteration':rows[-1][0], 'last_values':load_metrics(rows[-1][1:4],(0,0,1),280),
            'window_iterations':window,'mean_axis_torque_nm':mean,'relative_peak_to_peak':spread}


def residuals(text):
    result={}
    text=re.split(r'^Time = [^\n]+$',text,flags=re.MULTILINE)[-1]
    for field,value in re.findall(r'Solving for (\w+), Initial residual = ([^,\s]+)',text):
        value=float(value)
        if not math.isfinite(value) or value<0:
            raise ValueError('Nonfinite or negative residual.')
        result[field]=max(result.get(field,0),value)
    if set(result)!={'Ux','Uy','Uz','p','k','omega'} or not all(math.isfinite(v) for v in result.values()):
        raise ValueError('Missing or invalid residual records.')
    return result


def convergence_assessment(final_residuals,torque,planes):
    limits={'Ux':1e-4,'Uy':1e-4,'Uz':1e-4,'p':1e-3,'k':1e-4,'omega':1e-4}
    ordered=sorted(planes,key=float)
    flow_change=None
    if len(ordered)>=2:
        latest=planes[ordered[-1]]['downward_flow_cmm']; previous=planes[ordered[-2]]['downward_flow_cmm']
        flow_change=abs(latest-previous)/max(abs(latest),1e-12)
    checks={'residual_targets_met':all(final_residuals.get(k,float('inf'))<=v for k,v in limits.items()),
            'torque_window_stable':torque['relative_peak_to_peak']<=.02,
            'flow_snapshots_stable':flow_change is not None and flow_change<=.02}
    return {'status':'targets_met' if all(checks.values()) else 'not_converged',
            'checks':checks,'provisional_residual_limits':limits,'relative_stability_limit':.02,
            'flow_relative_change':flow_change,
            'note':'Development targets only. Does not qualify wall treatment, grid independence, or performance accuracy.'}


def iteration_diagnostics(text, interval=100):
    """Record sampled residuals and the latest wall/continuity evidence."""
    parts=re.split(r'^Time = ([0-9]+)\s*$',text,flags=re.MULTILINE)
    history=[]
    for step,block in zip(parts[1::2],parts[2::2]):
        if int(step)%interval==0:
            history.append({'iteration':int(step),'residuals':residuals(block)})
    walls={}
    for patch,low,high,mean in re.findall(r'patch (\w+) y\+ : min = ([\d.eE+-]+), max = ([\d.eE+-]+), average = ([\d.eE+-]+)',text):
        values=list(map(float,(low,high,mean)))
        if not all(math.isfinite(v) and v>=0 for v in values):
            raise ValueError('Invalid y-plus values.')
        walls[patch]=dict(zip(('min','max','average'),values))
    continuity=re.findall(r'time step continuity errors : sum local = ([\d.eE+-]+), global = ([\d.eE+-]+), cumulative = ([\d.eE+-]+)',text)
    return {'residual_history':history,'latest_y_plus':walls,
            'last_continuity_errors':dict(zip(('local','global','cumulative'),map(float,continuity[-1]))) if continuity else None}
