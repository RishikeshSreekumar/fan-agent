"""Read raw FAN-01 HDF5; preserve source names and flag inferred power units."""
from pathlib import Path
import sys,json,math,hashlib
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.reader-deps'))
import h5py

def channels(path):
    with h5py.File(path,'r') as f:
        result={name:obj[()].reshape(-1).tolist() for name,obj in f.items() if isinstance(obj,h5py.Dataset)}
    if not result or any(not all(math.isfinite(v) for v in values) for values in result.values()):
        raise ValueError('Missing or nonfinite experimental data.')
    return result

def main():
    path=ROOT/'extracted/characteristic/characteristic_n1ug.h5'
    raw=channels(path)
    keys=('volumetric_flow_in_m3_per_s','p_chamber_static_in_Pa','P_shaft_in_Nm')
    if set(raw)!=set(keys) or {len(raw[k]) for k in keys}!={20}:
        raise ValueError('Unexpected characteristic channels or sample count.')
    rows=[dict(zip(keys,values)) for values in zip(*(raw[k] for k in keys))]
    index=min(range(len(rows)),key=lambda i:abs(rows[i][keys[0]]-1.4))
    point=rows[index]; q,p,power=(point[k] for k in keys)
    lda={}
    for side in ('suction','pressure'):
        file=ROOT/f'extracted/lda_data/time_averaged/n1ug_1_4_time_averaged_{side}_side.h5'
        data=channels(file)
        if len({len(v) for v in data.values()})!=1:raise ValueError('Mismatched LDA array lengths.')
        lda[side]={'source':str(file.relative_to(ROOT)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'channels':data}
    result={'dataset_doi':'10.5281/zenodo.10787093','source':str(path.relative_to(ROOT)),
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'characteristic_raw':rows,
        'selected_index_zero_based':index,'selected_raw_point':point,'nominal_rpm_from_paper':1486,
        'unit_issue':{'channel':'P_shaft_in_Nm','status':'inferred_power_W_not_confirmed_metadata',
          'reason':'Interpreting this channel as W gives efficiency near the published 53%; interpreting it as torque does not. Preserve original labels.',
          'efficiency_if_power_W':q*p/power,'torque_Nm_if_power_W_and_1486rpm':power/(2*math.pi*1486/60),
          'strict_torque_validation_enabled':False},'lda_time_averaged':lda,
        'validation_status':'reference_imported_no_CFD_comparison'}
    (ROOT/'experimental-reference.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in result.items() if k not in ('characteristic_raw','lda_time_averaged')},indent=2))
if __name__=='__main__':main()
