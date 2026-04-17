from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="social-auto-upload local web console")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1 only)")
    parser.add_argument("--port", type=int, default=5050, help="Port (default: 5050)")
    args = parser.parse_args()

    try:
        from local_web.app import create_app
    except ModuleNotFoundError as exc:
        name = getattr(exc, "name", "") or ""
        if "flask" in name.lower():
            print('缺少 Web 依赖。请先执行: uv pip install -e ".[web]"')
            raise SystemExit(1) from exc
        raise

    app = create_app()
    print(f"\n  Local web UI:  http://{args.host}:{args.port}/\n  Press Ctrl+C to stop.\n")
    app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
