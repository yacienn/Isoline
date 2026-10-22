"""python -m isoline.server   (or: python -m isoline.webapp.main)"""
from __future__ import annotations

import argparse

from .config import Settings
from .container import build_app
from .interface.http_server import create_server


def main() -> None:
    defaults = Settings()
    ap = argparse.ArgumentParser(description="Isoline web interface")
    ap.add_argument("--host", default=defaults.host)
    ap.add_argument("--port", type=int, default=defaults.port)
    args = ap.parse_args()
    settings = Settings(host=args.host, port=args.port)
    server = create_server(settings.host, settings.port, build_app(settings))
    print(f"Isoline running at http://{settings.host}:{settings.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
