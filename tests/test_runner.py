import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch
from fan_agent.runner import HostError, Runner, _unpack

SSH = {'FAN_AGENT_CFD_BACKEND': 'ssh', 'FAN_AGENT_CFD_HOST': 'cfd@build01', 'FAN_AGENT_CFD_REMOTE_DIR': '/srv/fan-agent'}


def archive(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class ConfigurationTests(unittest.TestCase):
    def test_no_default_host_off_windows(self):
        with self.assertRaisesRegex(HostError, 'No CFD host configured'):
            Runner({}, platform='posix').check()

    def test_windows_defaults_to_wsl(self):
        runner = Runner({}, platform='nt').check()
        self.assertEqual(runner.backend, 'wsl')
        self.assertEqual(runner._command('bash', 'x.sh', [], '/w')[:5], ['wsl', '-d', 'Ubuntu', '--', 'bash'])

    def test_rejects_unsafe_settings(self):
        for env in ({**SSH, 'FAN_AGENT_CFD_HOST': '-oProxyCommand=x'}, {**SSH, 'FAN_AGENT_CFD_HOST': 'a;b'},
                    {**SSH, 'FAN_AGENT_CFD_REMOTE_DIR': 'relative'}, {**SSH, 'FAN_AGENT_CFD_SSH_PORT': '22;x'},
                    {**SSH, 'FAN_AGENT_CFD_DOCKER_IMAGE': 'img'},  # docker needs a run root
                    {**SSH, 'FAN_AGENT_CFD_DOCKER_IMAGE': 'img;rm', 'FAN_AGENT_RUN_ROOT': '/r'},
                    {'FAN_AGENT_CFD_BACKEND': 'wsl', 'FAN_AGENT_CFD_DOCKER_IMAGE': 'img', 'FAN_AGENT_RUN_ROOT': '/r'},
                    {'FAN_AGENT_CFD_BACKEND': 'local', 'FAN_AGENT_RUN_ROOT': '$(id)'}):
            with self.subTest(env=env), self.assertRaises(HostError):
                Runner(env, platform='posix').check()


class CommandTests(unittest.TestCase):
    def test_ssh_is_non_interactive_and_quoted(self):
        command = Runner(SSH, 'posix')._command('bash', 'mesh-demo.sh', ["a b"], '/w')
        self.assertEqual(command[:6], ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '--'])
        self.assertEqual(command[6], 'cfd@build01')
        self.assertEqual(command[7], "bash /srv/fan-agent/scripts/mesh-demo.sh 'a b'")

    def test_docker_mounts_scripts_and_run_root(self):
        env = {**SSH, 'FAN_AGENT_CFD_DOCKER_IMAGE': 'fan-agent-cfd:2412', 'FAN_AGENT_RUN_ROOT': '/srv/runs'}
        remote = Runner(env, 'posix').check()._command('bash', 'host-check.sh', [], '/srv/runs')[-1]
        self.assertIn('docker run --rm -u "$(id -u):$(id -g)"', remote)
        self.assertIn('/srv/fan-agent/scripts:/fan-agent/scripts:ro', remote)
        self.assertIn('-v /srv/runs:/srv/runs', remote)
        self.assertIn('FAN_AGENT_RUN_ROOT=/srv/runs', remote)
        self.assertTrue(remote.endswith('fan-agent-cfd:2412 bash /fan-agent/scripts/host-check.sh'))

    def test_local_run_root_exported(self):
        command = Runner({'FAN_AGENT_CFD_BACKEND': 'local', 'FAN_AGENT_RUN_ROOT': '/data/runs'}, 'posix')._command('bash', 'x.sh', [], '/w')
        self.assertEqual(command[:2], ['bash', '-c'])
        self.assertTrue(command[2].startswith('env FAN_AGENT_RUN_ROOT=/data/runs bash '))


class RemoteTransferTests(unittest.TestCase):
    def test_ssh_python_uploads_runs_fetches_and_cleans_up(self):
        calls = []
        def fake(command, **kwargs):
            calls.append(command[-1])
            if command[-1].startswith('tar -czf'):
                return CompletedProcess(command, 0, archive({'out.stl': b'solid', 'out.json': b'{}'}), b'')
            return CompletedProcess(command, 0, '' if kwargs.get('text') else b'', '' if kwargs.get('text') else b'')
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.runner.subprocess.run', side_effect=fake):
            source = Path(folder) / 'in.step'; source.write_bytes(b'ISO-10303-21;')
            result = Runner(SSH, 'posix').run_python('convert-step.py', [source], [Path(folder) / 'out.stl', Path(folder) / 'out.json'], timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertEqual((Path(folder) / 'out.stl').read_bytes(), b'solid')
        self.assertIn('mkdir -p /srv/fan-agent/scripts', calls[0])
        self.assertIn('/usr/bin/python3 /srv/fan-agent/scripts/convert-step.py /srv/fan-agent/jobs/', calls[2])
        self.assertTrue(calls[-1].startswith('rm -rf /srv/fan-agent/jobs/'))

    def test_cleanup_runs_after_failure_and_outputs_not_fetched(self):
        calls = []
        def fake(command, **kwargs):
            calls.append(command[-1])
            code = 1 if 'convert-step.py' in command[-1] else 0
            return CompletedProcess(command, code, '' if kwargs.get('text') else b'', '' if kwargs.get('text') else b'')
        with tempfile.TemporaryDirectory() as folder, patch('fan_agent.runner.subprocess.run', side_effect=fake):
            source = Path(folder) / 'in.step'; source.write_bytes(b'x')
            result = Runner(SSH, 'posix').run_python('convert-step.py', [source], [Path(folder) / 'out.stl'], timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((Path(folder) / 'out.stl').exists())
        self.assertFalse(any(c.startswith('tar -czf') for c in calls))
        self.assertTrue(calls[-1].startswith('rm -rf '))

    def test_unpack_only_accepts_expected_regular_files(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(KeyError):
                _unpack(archive({'../evil': b'x'}), folder, ['out.stl'])
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
                info = tarfile.TarInfo('out.stl'); info.type = tarfile.SYMTYPE; info.linkname = '/etc/passwd'
                tar.addfile(info)
            with self.assertRaises(HostError):
                _unpack(buffer.getvalue(), folder, ['out.stl'])
