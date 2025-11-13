#!/usr/bin/env python3
"""
Git Workflow Guardian - Dashboard Launcher
Start the compliance dashboard web interface
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from service.dashboard import start_dashboard


def main():
    parser = argparse.ArgumentParser(
        description="Git Workflow Guardian - Compliance Dashboard"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode"
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Make dashboard accessible from network (binds to 0.0.0.0)"
    )

    args = parser.parse_args()

    host = "0.0.0.0" if args.public else args.host

    print("=" * 60)
    print("🛡️  Git Workflow Guardian - Compliance Dashboard")
    print("=" * 60)
    print()

    if args.public:
        print("⚠️  WARNING: Dashboard is accessible from network!")
        print()

    start_dashboard(host=host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
