"""Where fixed CFD/CAD workers execute. Only repository scripts and generated paths reach a host.

Backends, chosen by FAN_AGENT_CFD_BACKEND:
  wsl    Windows host; scripts run in a WSL distribution (default on Windows).
  local  This machine is the Linux CFD host.
  ssh    Remote Linux host (FAN_AGENT_CFD_HOST); scripts and inputs are copied over first.
With local or ssh, FAN_AGENT_CFD_DOCKER_IMAGE runs each command inside that image
(see docker/Dockerfile); FAN_AGENT_RUN_ROOT is then required so run folders persist.
Other platforms have no default: CFD must not run on an unconfigured workstation.
"""
import io
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
BACKENDS = ("wsl", "local", "ssh")
CONTAINER_SCRIPTS = "/fan-agent/scripts"
LINUX_PATH = r"/[A-Za-z0-9/._-]*"


class HostError(ValueError):
    pass


def wsl_path(path):
    path = Path(path).resolve()
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:] if path.drive else str(path)


def _pack(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, path in files:
            archive.add(str(path), arcname=name, recursive=False)
    return buffer.getvalue()


def _unpack(data, folder, names):
    """Extract only the expected regular files; never trust archive paths."""
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for name in names:
            member = archive.getmember(name)
            if not member.isfile():
                raise HostError("Remote output is not a regular file.")
            (Path(folder) / name).write_bytes(archive.extractfile(member).read())


class Runner:
    def __init__(self, env=None, platform=None):
        env = os.environ if env is None else env
        platform = os.name if platform is None else platform
        self.backend = env.get("FAN_AGENT_CFD_BACKEND", "").strip().lower() or ("wsl" if platform == "nt" else "")
        self.distro = env.get("FAN_AGENT_WSL_DISTRO", "Ubuntu").strip()
        self.host = env.get("FAN_AGENT_CFD_HOST", "").strip()
        self.port = env.get("FAN_AGENT_CFD_SSH_PORT", "").strip()
        self.remote_dir = env.get("FAN_AGENT_CFD_REMOTE_DIR", "").strip()
        self.image = env.get("FAN_AGENT_CFD_DOCKER_IMAGE", "").strip()
        self.run_root = env.get("FAN_AGENT_RUN_ROOT", "").strip()

    def check(self):
        if self.backend not in BACKENDS:
            raise HostError("No CFD host configured. Set FAN_AGENT_CFD_BACKEND to wsl, local or ssh; "
                            "this workstation does not run CFD by default.")
        if self.backend == "wsl" and not re.fullmatch(r"[A-Za-z0-9._-]+", self.distro):
            raise HostError("Invalid FAN_AGENT_WSL_DISTRO.")
        if self.backend == "ssh":
            if not re.fullmatch(r"(?:[A-Za-z0-9._-]+@)?[A-Za-z0-9.-]+", self.host) or self.host.startswith("-"):
                raise HostError("Set FAN_AGENT_CFD_HOST to host or user@host for the ssh backend.")
            if self.port and not self.port.isdigit():
                raise HostError("FAN_AGENT_CFD_SSH_PORT must be a number.")
            if not re.fullmatch(LINUX_PATH, self.remote_dir) or len(self.remote_dir) < 2:
                raise HostError("Set FAN_AGENT_CFD_REMOTE_DIR to an absolute remote path for the ssh backend.")
        if self.image:
            if self.backend == "wsl" or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9./:_@-]*", self.image):
                raise HostError("FAN_AGENT_CFD_DOCKER_IMAGE needs the local or ssh backend and a plain image name.")
            if not self.run_root:
                raise HostError("Set FAN_AGENT_RUN_ROOT (absolute host path) so container run folders persist.")
        if self.run_root and not re.fullmatch(LINUX_PATH, self.run_root):
            raise HostError("FAN_AGENT_RUN_ROOT must be an absolute Linux path.")
        return self

    def describe(self):
        return {"backend": self.backend or None, "host": self.host or None,
                "wsl_distro": self.distro if self.backend == "wsl" else None,
                "docker_image": self.image or None, "remote_dir": self.remote_dir or None,
                "run_root": self.run_root or None}

    # Command construction -------------------------------------------------
    def _ssh(self, remote_command):
        port = ["-p", self.port] if self.port else []
        return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", *port, "--", self.host, remote_command]

    def _host_scripts(self):
        """Script folder as seen by the Linux host (outside any container)."""
        if self.backend == "ssh":
            return str(PurePosixPath(self.remote_dir) / "scripts")
        return wsl_path(SCRIPTS) if self.backend == "wsl" else str(SCRIPTS)

    def _command(self, interpreter, name, args, workdir):
        """Full argv that runs scripts/<name> on the configured host (and container)."""
        env = {"FAN_AGENT_RUN_ROOT": self.run_root} if self.run_root else {}
        if self.image:
            script = f"{CONTAINER_SCRIPTS}/{name}"
            docker = ["docker", "run", "--rm", "--entrypoint", "", "-w", workdir, "-e", "HOME=/tmp",
                      "-v", f"{self._host_scripts()}:{CONTAINER_SCRIPTS}:ro"]
            for mount in dict.fromkeys([workdir, self.run_root]):
                docker += ["-v", f"{mount}:{mount}"]
            for key, value in env.items():
                docker += ["-e", f"{key}={value}"]
            quoted = " ".join(shlex.quote(p) for p in [*docker, self.image, interpreter, script, *args])
            # Run as the host user so case files stay editable outside the container.
            command = quoted.replace("docker run --rm", 'docker run --rm -u "$(id -u):$(id -g)"', 1)
        else:
            script = str(PurePosixPath(self._host_scripts()) / name)
            prefix = ["env", *(f"{k}={v}" for k, v in env.items())] if env else []
            command = " ".join(shlex.quote(p) for p in [*prefix, interpreter, script, *args])
        if self.backend == "ssh":
            return self._ssh(command)
        if self.backend == "wsl":
            return ["wsl", "-d", self.distro, "--", "bash", "-c", command]
        return ["bash", "-c", command]

    def _sync_scripts(self):
        files = [(p.name, p) for p in sorted(SCRIPTS.iterdir()) if p.is_file() and p.suffix != ".pyc"]
        target = shlex.quote(self._host_scripts())
        result = subprocess.run(self._ssh(f"mkdir -p {target} && tar -xzf - -C {target}"),
                                input=_pack(files), capture_output=True, timeout=120)
        if result.returncode:
            raise HostError("Could not copy worker scripts to the CFD host: "
                            + result.stderr.decode(errors="replace")[-500:])

    # Public operations ----------------------------------------------------
    def run_script(self, name, timeout, args=()):
        """Run a fixed bash script from scripts/; case folders stay on the CFD host."""
        self.check()
        if self.backend == "ssh":
            self._sync_scripts()
        workdir = self.run_root or self._host_scripts()
        return subprocess.run(self._command("bash", name, args, workdir), capture_output=True, text=True, timeout=timeout)

    def run_python(self, name, inputs, outputs, timeout):
        """Run scripts/<name> with input then output file paths as arguments.

        All files share one local folder. The worker sees host paths; on ssh, inputs are
        uploaded to a temporary job folder and outputs copied back only on success.
        """
        self.check()
        files = [Path(p).resolve() for p in (*inputs, *outputs)]
        if len({p.parent for p in files}) != 1:
            raise HostError("Worker inputs and outputs must share one folder.")
        if self.backend != "ssh":
            host = [wsl_path(p) if self.backend == "wsl" else str(p) for p in files]
            workdir = str(PurePosixPath(host[0]).parent)
            return subprocess.run(self._command("/usr/bin/python3", name, host, workdir), capture_output=True, text=True, timeout=timeout)
        self._sync_scripts()
        job = str(PurePosixPath(self.remote_dir) / "jobs" / uuid.uuid4().hex)
        upload = subprocess.run(self._ssh(f"mkdir -p {shlex.quote(job)} && tar -xzf - -C {shlex.quote(job)}"),
                                input=_pack([(Path(p).name, p) for p in inputs]), capture_output=True, timeout=120)
        if upload.returncode:
            raise HostError("Could not copy inputs to the CFD host.")
        try:
            remote = [str(PurePosixPath(job) / p.name) for p in files]
            result = subprocess.run(self._command("/usr/bin/python3", name, remote, job), capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0 and outputs:
                names = [Path(p).name for p in outputs]
                fetch = subprocess.run(self._ssh(f"tar -czf - -C {shlex.quote(job)} " + " ".join(map(shlex.quote, names))),
                                       capture_output=True, timeout=120)
                if fetch.returncode:
                    raise HostError("Could not copy outputs back from the CFD host.")
                _unpack(fetch.stdout, files[0].parent, names)
            return result
        finally:
            subprocess.run(self._ssh(f"rm -rf {shlex.quote(job)}"), capture_output=True, timeout=60)

    def host_check(self, timeout=120):
        """Confirm the host has OpenFOAM v2412 and Python Gmsh. Runs no case."""
        return self.run_script("host-check.sh", timeout=timeout)
