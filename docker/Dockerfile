# Fan-Agent CFD worker: OpenCFD OpenFOAM v2412 plus system-Python Gmsh.
# Scripts are not baked in; the runner mounts the repository scripts read-only at /fan-agent/scripts.
# Build on the CFD host:  docker build -t fan-agent-cfd:2412 docker/
FROM opencfd/openfoam-default:2412

USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-gmsh m4 \
 && rm -rf /var/lib/apt/lists/*

# The runner overrides the entrypoint and user; scripts source the OpenFOAM bashrc themselves.
ENTRYPOINT []
CMD ["bash"]
