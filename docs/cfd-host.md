# CFD host configuration

Fan-Agent never runs OpenFOAM or Gmsh on an unconfigured machine. The UI/server can run anywhere; the
fixed worker scripts in `scripts/` run on the CFD host selected by environment variables. Designer
input never reaches a shell: only repository scripts and generated file names are passed.

Check any configuration with `python -m fan_agent host-check`. It confirms OpenFOAM v2412, the
OpenFOAM tools used by the scripts, Python Gmsh, `m4` and a writable run root. It creates no case.

| Variable | Used by | Meaning |
|---|---|---|
| `FAN_AGENT_CFD_BACKEND` | all | `wsl`, `local` or `ssh`. Defaults to `wsl` on Windows; no default elsewhere. |
| `FAN_AGENT_WSL_DISTRO` | wsl | WSL distribution, default `Ubuntu`. |
| `FAN_AGENT_CFD_HOST` | ssh | `host` or `user@host`. Key-based login required (`BatchMode=yes`). |
| `FAN_AGENT_CFD_SSH_PORT` | ssh | Optional port. |
| `FAN_AGENT_CFD_REMOTE_DIR` | ssh | Absolute remote folder; `scripts/` and `fan_agent/` are copied there, STEP jobs use `jobs/` and are deleted afterwards. |
| `FAN_AGENT_CFD_DOCKER_IMAGE` | local, ssh | Run each worker inside this image (see `docker/Dockerfile`). |
| `FAN_AGENT_RUN_ROOT` | all; required with Docker | Absolute Linux folder for `fan-agent-*` case folders. Default `$HOME` on the host. |

## 1. Windows + WSL (current)

Unchanged behaviour: run the server on Windows. OpenFOAM v2412 at `/usr/lib/openfoam/openfoam2412`
and `python3-gmsh` in WSL Ubuntu. No variables needed.

## 2. Remote Linux server over SSH

On the server: install OpenFOAM v2412 (OpenCFD apt repository) and `python3-gmsh m4`, or use Docker (3).
On the machine running Fan-Agent:

```
FAN_AGENT_CFD_BACKEND=ssh
FAN_AGENT_CFD_HOST=cfd@build01
FAN_AGENT_CFD_REMOTE_DIR=/srv/fan-agent
```

Case folders and logs stay on the server under `$HOME` (or `FAN_AGENT_RUN_ROOT`). STEP conversion
uploads the CAD, converts it and copies the STL and metadata back.

## 3. Docker on the Linux server

```
docker build -t fan-agent-cfd:2412 docker/     # on the server, from a copy of this repository
FAN_AGENT_CFD_DOCKER_IMAGE=fan-agent-cfd:2412
FAN_AGENT_RUN_ROOT=/srv/fan-agent/runs          # must exist and be writable by the ssh user
```

Combine with the ssh variables above. Containers run as the ssh user with the repository copy mounted
read-only. The image build and Docker path have not yet been exercised on a real host; run
`host-check` first and record the result.
