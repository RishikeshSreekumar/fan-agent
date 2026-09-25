import unittest
from fan_agent.cell_slice import tetra_polygon
from fan_agent.solver_results import torque_summary,residuals,convergence_assessment,iteration_diagnostics


class SolverResultTests(unittest.TestCase):
    def test_final_iteration_uses_worst_pressure_correction(self):
        log='Time = 1\nSolving for p, Initial residual = 0.9\nTime = 2\n'
        log+='\n'.join(f'Solving for {field}, Initial residual = 0.01' for field in ['Ux','Uy','Uz','p','k','omega'])
        log+='\nSolving for p, Initial residual = 0.001\nExecutionTime = 2 s\nEnd'
        self.assertEqual(residuals(log)['p'],.01)

    def test_cube_slice_covers_full_area(self):
        p=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
        tets=[(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6)]
        self.assertAlmostEqual(sum(tetra_polygon([p[i] for i in t],.5)[1] for t in tets),1)

    def test_stable_torque_does_not_hide_changing_flow(self):
        result=convergence_assessment(dict.fromkeys(['Ux','Uy','Uz','p','k','omega'],1e-6),
                                      {'relative_peak_to_peak':.001},{'100':{'downward_flow_cmm':100},'200':{'downward_flow_cmm':200}})
        self.assertEqual(result['status'],'not_converged')

    def test_exact_tetra_slice(self):
        polygon,area=tetra_polygon([(0,0,0),(1,0,0),(0,1,0),(0,0,2)],1)
        self.assertEqual(len(polygon),3)
        self.assertAlmostEqual(area,.125)
        self.assertEqual(tetra_polygon([(0,0,0),(1,0,0),(0,1,0),(0,0,2)],3)[1],0)

    def test_vertex_tangency_has_zero_area(self):
        self.assertEqual(tetra_polygon([(0,0,0),(1,0,0),(0,1,0),(0,0,2)],2)[1],0)

    def test_torque_drift_is_not_hidden_by_last_value(self):
        history='\n'.join(f'{i} 0 0 {i} 0 0 {i} 0 0 0' for i in range(1,51))
        self.assertGreater(torque_summary(history)['relative_peak_to_peak'],1)

    def test_missing_residuals_rejected(self):
        with self.assertRaises(ValueError):residuals('End')

    def test_nonfinite_correction_cannot_be_hidden(self):
        log='\n'.join(f'Solving for {f}, Initial residual = 0.01' for f in ['Ux','Uy','Uz','p','k','omega'])
        for invalid in ('nan','inf','-1'):
            with self.assertRaises(ValueError):
                residuals(log+f'\nSolving for p, Initial residual = {invalid}')

    def test_diagnostic_history_ignores_execution_time(self):
        block='\n'.join(f'Solving for {f}, Initial residual = 0.01' for f in ['Ux','Uy','Uz','p','k','omega'])
        log='Time = 100\n'+block+'\nExecutionTime = 100 s\npatch fan y+ : min = 3, max = 600, average = 150\n'
        report=iteration_diagnostics(log)
        self.assertEqual(len(report['residual_history']),1)
        self.assertEqual(report['latest_y_plus']['fan']['max'],600)

    def test_long_torque_drift_visible_despite_stable_tail(self):
        history='\n'.join(f'{i} 0 0 {2 if i<250 else 1} 0 0 0 0 0 0' for i in range(500))
        report=torque_summary(history)
        self.assertEqual(report['relative_peak_to_peak'],0)
        self.assertEqual(report['long_window_drift']['relative_change'],1)
