import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fan_agent.cad import convert_step


@patch.dict(os.environ, {'FAN_AGENT_CFD_BACKEND': 'local'})
class CadFailureTests(unittest.TestCase):
    def test_rejects_non_step_before_launch(self):
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.runner.subprocess.run') as run:
            with self.assertRaises(ValueError):
                convert_step(b'not CAD', folder)
            run.assert_not_called()
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_failed_conversion_retains_source_and_log(self):
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.runner.subprocess.run') as run:
            run.return_value.returncode = 1
            run.return_value.stdout = ''
            run.return_value.stderr = 'invalid solid'
            data = b'ISO-10303-21; invalid test'
            with self.assertRaises(ValueError):
                convert_step(data, folder)
            self.assertEqual(next(Path(folder).glob('*.step')).read_bytes(), data)
            self.assertIn('invalid solid', next(Path(folder).glob('*.log')).read_text())

    def test_unconfigured_host_refuses_before_writing(self):
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.runner.subprocess.run') as run, \
                patch.dict(os.environ, {'FAN_AGENT_CFD_BACKEND': ''}), patch('fan_agent.runner.os.name', 'posix'):
            with self.assertRaisesRegex(ValueError, 'No CFD host configured'):
                convert_step(b'ISO-10303-21; test', folder)
            run.assert_not_called()
            self.assertEqual(list(Path(folder).iterdir()), [])
