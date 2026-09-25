import math
import random
import tempfile
import unittest
from pathlib import Path
from fan_agent.convergence import assess, moment_series, residual_series, surface_series, window_stability
from fan_agent.gci import three_grid
from fan_agent.recipe import CONVERGENCE, MESH_LEVELS, case_files, mesh_sizes, omega_rad_s, write_case
from fan_agent.runner import HostError, Runner
from fan_agent.runtime import combine_levels


class RecipeFileTests(unittest.TestCase):
    def test_rotation_sign_and_speed(self):
        self.assertAlmostEqual(omega_rad_s(280, 'cw'), -29.3215314335, places=8)  # retained baseline value
        self.assertGreater(omega_rad_s(280, 'ccw'), 0)
        for rpm, direction in ((0, 'cw'), (4000, 'cw'), (True, 'cw'), (float('nan'), 'cw'), (280, 'up')):
            with self.subTest(rpm=rpm, direction=direction), self.assertRaises(ValueError):
                omega_rad_s(rpm, direction)

    def test_wall_treatment_and_stages(self):
        files = case_files(280, 'cw')
        self.assertIn('nutUSpaldingWallFunction', files['0/nut'])
        self.assertIn('blending tanh', files['0/omega'])
        self.assertIn('bounded Gauss upwind', files['system/fvSchemes'].split('div(phi,U)')[1].split(';')[0])
        self.assertIn('linearUpwind grad(U)', files['system/fvSchemes.stage2'])
        self.assertIn(f"endTime {CONVERGENCE['stage1_iterations']};", files['system/controlDict'])
        self.assertIn('omega -29.3215314', files['constant/MRFProperties'])
        self.assertIn('radius 0.684', files['system/topoSetDict'])
        self.assertIn('bounds ((-0.57 -0.57 1.19) (0.57 0.57 1.21))', files['system/controlDict'])
        for name in ('U', 'p', 'k', 'omega', 'nut'):
            self.assertEqual(files['0/' + name].count('type '), 4)

    def test_braces_balance_and_files_written(self):
        files = case_files(250, 'ccw', procs=4)
        for name, text in files.items():
            self.assertEqual(text.count('{'), text.count('}'), name)
            self.assertEqual(text.count('('), text.count(')'), name)
        self.assertIn('numberOfSubdomains 4;', files['system/decomposeParDict'])
        with tempfile.TemporaryDirectory() as root:
            write_case(root, 250, 'ccw')
            self.assertTrue((Path(root) / 'system/fvSolution.stage2').exists())

    def test_mesh_levels_are_systematic(self):
        medium, fine, coarse = mesh_sizes('medium'), mesh_sizes('fine'), mesh_sizes('coarse')
        self.assertEqual(medium['near_fan'], .012)
        for key in medium:
            self.assertAlmostEqual(coarse[key] / medium[key], medium[key] / fine[key])
        self.assertGreaterEqual(MESH_LEVELS['coarse'], 1.3)
        with self.assertRaises(ValueError):
            mesh_sizes('ultra')


def series(values, start=1):
    return [(start + i, v) for i, v in enumerate(values)]


class ConvergenceTests(unittest.TestCase):
    settings = dict(CONVERGENCE, stage1_iterations=10, window=50)

    def test_parsers_merge_restarts(self):
        first = '# Time total_x total_y total_z p_x p_y p_z v_x v_y v_z\n1 0 0 1.5 0 0 1.4 0 0 .1\n2 0 0 1.6 0 0 1.5 0 0 .1\n'
        second = '2 0 0 1.7 0 0 1.6 0 0 .1\n3 0 0 1.8 0 0 1.7 0 0 .1\n'
        self.assertEqual(moment_series([first, second]), [(1, 1.5), (2, 1.7), (3, 1.8)])
        self.assertEqual(surface_series(['# Area : 1.2\n# Time areaNormalIntegrate(U)\n5\t-0.25\n']), [(5, -.25)])
        with self.assertRaises(ValueError):
            moment_series(['1 2 3\n'])
        with self.assertRaises(ValueError):
            surface_series(['1 nan\n'])

    def test_residual_series(self):
        log = 'Time = 1\n\nsmoothSolver:  Solving for Ux, Initial residual = 0.5, Final\nGAMG:  Solving for p, Initial residual = 0.2, Final\nGAMG:  Solving for p, Initial residual = 0.3, Final\nTime = 2\n\nsmoothSolver:  Solving for Ux, Initial residual = 0.4, Final\n'
        self.assertEqual(residual_series(log), [(1, {'Ux': .5, 'p': .3}), (2, {'Ux': .4})])

    def test_oscillating_but_stable_monitors_pass(self):
        rng = random.Random(1)
        torque = series([1.8 + .02 * math.sin(i / 3) + rng.uniform(-.005, .005) for i in range(200)])
        flow = series([-60 + .5 * math.sin(i / 5) for i in range(200)])
        history = series([{'p': 4e-3, 'Ux': 1e-3} for _ in range(200)])
        result = assess(torque, flow, history, self.settings)
        self.assertEqual(result['status'], 'stable')
        self.assertLess(result['torque']['relative_change'], .01)
        self.assertGreater(result['torque']['relative_half_range'], 0)

    def test_drift_is_not_converged(self):
        torque = series([1.8 + .001 * i for i in range(200)])
        flow = series([-60.0] * 200)
        history = series([{'p': 1e-3}] * 200)
        self.assertEqual(assess(torque, flow, history, self.settings)['status'], 'not_converged')

    def test_growing_residuals_are_diverging(self):
        flat = series([1.0] * 200)
        history = series([{'p': 1e-3 * (1.01 ** i)} for i in range(200)])
        self.assertEqual(assess(flat, flat, history, self.settings)['status'], 'diverging')

    def test_too_short_after_stage1(self):
        check = window_stability(series([1.0] * 100), 10, 50, .01)
        self.assertFalse(check['stable'])
        self.assertIn('Needs 100 samples', check['reason'])


class GciTests(unittest.TestCase):
    def test_celik_worked_example(self):
        # Celik et al. (2008) Table 1, column phi = 6.063/5.972/5.863 with r21 = 1.5 and r32 = 1.333 (3D cell counts).
        cells = [1_000_000, round(1_000_000 / 1.5 ** 3), round(1_000_000 / 1.5 ** 3 / (4 / 3) ** 3)]
        result = three_grid(cells, [6.063, 5.972, 5.863], 1.0)
        self.assertEqual(result['convergence'], 'monotonic')
        self.assertAlmostEqual(result['order'], 1.53, delta=.01)
        self.assertAlmostEqual(result['extrapolated'], 6.1685, delta=.001)
        self.assertAlmostEqual(result['gci_fine'], .022, delta=.001)
        self.assertTrue(result['accepted'])

    def test_oscillatory_divergent_and_invalid(self):
        self.assertEqual(three_grid([8000, 3000, 1000], [1.0, 1.1, 0.95], 1)['convergence'], 'oscillatory')
        self.assertEqual(three_grid([8000, 3000, 1000], [1.0, 1.2, 1.25], 1)['convergence'], 'divergent')
        for cells in ([1000, 3000, 8000], [8000, 3000], [8000, 3000, 0]):
            with self.subTest(cells=cells), self.assertRaises(ValueError):
                three_grid(cells, [1, 1, 1][:len(cells)], 1)


def level(name, cells, torque, flow, status='stable', rpm=280):
    return {'recipe': 'mrf-sst-v2412-screening-1', 'level': name, 'rpm': rpm, 'direction': 'cw', 'cells': cells,
            'fluid_volume_m3': 48.0, 'mesh_check_passed': True, 'convergence': {'status': status},
            'monitors': {'axis_torque_nm': torque, 'jet_flow_cmm': flow}, 'case': '/x'}


class CombineTests(unittest.TestCase):
    def test_passes_with_small_gci(self):
        results = {'fine': level('fine', 460000, 1.80, 100.0), 'medium': level('medium', 168000, 1.79, 99.0),
                   'coarse': level('coarse', 61000, 1.76, 96.5)}
        summary = combine_levels(results)
        self.assertEqual(summary['status'], 'mesh_study_passed', summary)

    def test_blocks_incomplete_unstable_and_mixed(self):
        self.assertEqual(combine_levels({'fine': level('fine', 3, 1, 1)})['status'], 'incomplete')
        unstable = {'fine': level('fine', 3, 1, 1, 'not_converged'), 'medium': level('medium', 2, 1, 1), 'coarse': level('coarse', 1, 1, 1)}
        self.assertEqual(combine_levels(unstable)['status'], 'blocked')
        mixed = {'fine': level('fine', 3, 1, 1, rpm=250), 'medium': level('medium', 2, 1, 1), 'coarse': level('coarse', 1, 1, 1)}
        self.assertEqual(combine_levels(mixed)['status'], 'inconsistent')


class ForwardingTests(unittest.TestCase):
    def test_solver_settings_forwarded_and_validated(self):
        env = {'FAN_AGENT_CFD_BACKEND': 'local', 'FAN_AGENT_CFD_PROCS': '8'}
        command = Runner(env, 'posix').check()._command('bash', 'recipe-case.sh', ['fine', '280', 'cw'], '/w')
        self.assertIn('env FAN_AGENT_CFD_PROCS=8 bash', command[2])
        with self.assertRaises(HostError):
            Runner(dict(env, FAN_AGENT_CFD_PROCS='8; rm'), 'posix').check()
