import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fan_agent.cad import convert_step


class CadFailureTests(unittest.TestCase):
    def test_rejects_non_step_before_launch(self):
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.cad.subprocess.run') as run:
            with self.assertRaises(ValueError):
                convert_step(b'not CAD', folder)
            run.assert_not_called()
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_failed_conversion_retains_source_and_log(self):
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.cad.subprocess.run') as run:
            run.return_value.returncode = 1
            run.return_value.stdout = ''
            run.return_value.stderr = 'invalid solid'
            data = b'ISO-10303-21; invalid test'
            with self.assertRaises(ValueError):
                convert_step(data, folder)
            self.assertEqual(next(Path(folder).glob('*.step')).read_bytes(), data)
            self.assertIn('invalid solid', next(Path(folder).glob('*.log')).read_text())
