"""Three live, generic ceiling-fan checks through the local app; no CAD or solver calls."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CASES = [
    ('complete', 'Compare a 1200 mm ceiling fan at 250 and 300 RPM in a 4 m by 4 m by 3 m room. Rotor height is 2.5 m above the floor; sampling height is 1.2 m above the floor. Rotation is clockwise viewed from above.'),
    ('missing', 'Compare this ceiling fan at 250 and 300 RPM.'),
    ('unsupported', 'For this ceiling fan, change the blade pitch by 5 degrees and run a transient sliding-mesh AMI simulation. Predict the resulting torque now.'),
]

def evaluate(name, proposal):
    checks = {'execution_blocked': proposal.get('can_run') is False,
              'no_results': 'results' in proposal and proposal['results'] is None}
    if name == 'complete':
        cases = proposal.get('cases', [])
        checks['two_requested_speeds'] = [c.get('rpm') for c in cases] == [250, 300]
        expected = dict(diameter_mm=1200, room_x_m=4, room_y_m=4, room_z_m=3,
                        rotor_height_m=2.5, sampling_height_m=1.2, direction='cw')
        checks['explicit_values_preserved'] = len(cases) == 2 and all(all(c.get(k) == v for k,v in expected.items()) for c in cases)
        checks['ready_for_review'] = proposal.get('status') == 'proposal_ready'
    elif name == 'missing':
        checks['requests_missing_inputs'] = proposal.get('status') == 'needs_inputs' and not proposal.get('cases')
        inputs = proposal.get('inputs', {})
        checks['no_invented_values'] = all(k in inputs and inputs[k] is None for k in ('diameter_mm','room_x_m','room_y_m','room_z_m','rotor_height_m','sampling_height_m','direction'))
        checks['requested_speeds_preserved'] = inputs.get('rpms') == [250, 300]
    elif name == 'unsupported':
        checks['unsupported_work_blocked'] = proposal.get('status') == 'unsupported' and bool(proposal.get('unsupported')) and not proposal.get('cases')
    else:
        raise ValueError('Unknown check')
    return checks

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    base = f'http://127.0.0.1:{args.port}'
    def get(path):
        with urlopen(base+path, timeout=5) as response:
            return json.load(response)
    try:
        status = get('/api/ai/status')
    except (URLError, OSError, ValueError):
        print('Local server unavailable. Start start-ai.ps1 with your key, then retry. No model requests made.')
        return 2
    if not status.get('configured'):
        print('Configure the AI provider in start-ai.ps1 first. No model requests made.')
        return 2
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'provider': status['provider'],
              'model': status['model'], 'live': True, 'checks': [],
              'scope': 'Three generic prompts only; no geometry, case creation or solver requests.'}
    for name, prompt in CASES:
        item = {'name': name, 'prompt': prompt}
        request = Request(base+'/api/studies/propose',data=json.dumps({'prompt':prompt}).encode(),headers={'Content-Type':'application/json'})
        try:
            with urlopen(request,timeout=60) as response:
                proposal = json.load(response)
            item['proposal'] = proposal
            item['checks'] = evaluate(name,proposal)
            item['passed'] = all(item['checks'].values())
        except (HTTPError, URLError, OSError, ValueError, TypeError, AttributeError) as exc:
            # Do not save arbitrary provider response bodies or environment values.
            item.update(passed=False, error=f'{type(exc).__name__}: request failed; inspect the app configuration/error display.')
        report['checks'].append(item)
        print(name+': '+('PASS' if item['passed'] else 'FAIL'),flush=True)
        if 'error' in item:
            break  # Do not burn quota retrying connection/authentication failures.
    report['passed'] = len(report['checks']) == len(CASES) and all(i['passed'] for i in report['checks'])
    root = Path(__file__).resolve().parents[1]/'docs'/'ai-live-checks'
    root.mkdir(exist_ok=True)
    target=root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    target.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('Evidence: '+str(target))
    print('This checks observed model extraction, not CFD accuracy.')
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
