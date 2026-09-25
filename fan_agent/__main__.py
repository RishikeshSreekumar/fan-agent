import argparse

from .server import make_server


def main():
    parser = argparse.ArgumentParser(description="Fan-Agent local workbench")
    parser.add_argument("command", choices=["serve", "host-check", "runtime-smoke", "mesh-demo", "cad-mesh-demo"])
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command in {"host-check", "runtime-smoke", "mesh-demo", "cad-mesh-demo"}:
        from .runtime import smoke
        raise SystemExit(smoke(mesh=args.command == "mesh-demo", cad=args.command == "cad-mesh-demo",
                               host=args.command == "host-check"))
    server = make_server(args.port)
    print(f"Fan-Agent: http://127.0.0.1:{server.server_address[1]} — Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
