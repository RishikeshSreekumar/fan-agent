import unittest
from fan_agent.mesh_report import summarize
from fan_agent.runtime import mesh_diagnostics_from_output


class MeshReportTests(unittest.TestCase):
    def test_stage_log_echo_cannot_replace_final_mesh(self):
        output = 'MESH_DIAGNOSTICS_JSON={"stage":"final","count":1808}\nMESH_DIAGNOSTICS_JSON={"stage":"snapped","count":1503}\n'
        self.assertEqual(mesh_diagnostics_from_output(output)['count'], 1808)
        self.assertIsNone(mesh_diagnostics_from_output('MESH_DIAGNOSTICS_JSON={"stage":"snapped"}'))

    def test_completed_mesher_does_not_override_failed_quality(self):
        report = summarize('Failed 1 mesh checks.\nEnd\n', 'Finished meshing without any errors', 'cellZoneSet rotor now size 32')
        self.assertFalse(report['extended_mesh_check_passed'])
        self.assertFalse(report['accepted_for_solver'])
        self.assertEqual(report['rotor_cells'], 32)

    def test_layer_thickness_is_not_coverage(self):
        report = summarize('Mesh OK.\n', 'fan 2434 3 1.34 0.00454 38.5\n', '')
        self.assertEqual(report['layers']['mean_layers'], 1.34)
        self.assertEqual(report['layers']['thickness_percent_of_requested'], 38.5)
        self.assertIsNone(report['rotor_cells'])
        self.assertFalse(report['accepted_for_solver'])

    def test_absent_evidence_fails_closed(self):
        report = summarize('', '', '')
        self.assertFalse(report['extended_mesh_check_passed'])
        self.assertIsNone(report['concave_cells'])

    def test_no_layers_cannot_pass_development_gate(self):
        report = summarize('Mesh OK.\nMin volume = 5.4317003e-08. Max volume = 1.',
                           'Writing 0 added cells to cellSet addedCells', 'cellZoneSet rotor now size 10')
        self.assertFalse(report['development_gate_passed'])
        self.assertEqual(report['min_volume_m3'], 5.4317003e-08)

    def test_valid_development_mesh_is_not_solver_qualification(self):
        report = summarize('Mesh OK.\n', 'Writing 40 added cells to cellSet addedCells', 'cellZoneSet rotor now size 10')
        self.assertTrue(report['development_gate_passed'])
        self.assertFalse(report['accepted_for_solver'])
