#!/usr/bin/env python3
"""
MIMIC V3.1 Dashboard Standalone Runner
Bloomberg-style terminal monitor in demo mode

Usage:
    python run_dashboard.py                    # Default port 8080
    python run_dashboard.py --port 3000        # Custom port
    python run_dashboard.py --host 127.0.0.1   # Localhost only
"""

import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(
        description="MIMIC V3.1 Bloomberg-Style Dashboard"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )

    args = parser.parse_args()

    # Import and run dashboard
    from dashboard import run_dashboard

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███╗   ███╗██╗███╗   ███╗██╗ ██████╗    ██╗   ██╗██████╗    ██╗           ║
║    ████╗ ████║██║████╗ ████║██║██╔════╝    ██║   ██║╚════██╗  ███║           ║
║    ██╔████╔██║██║██╔████╔██║██║██║         ██║   ██║ █████╔╝  ╚██║           ║
║    ██║╚██╔╝██║██║██║╚██╔╝██║██║██║         ╚██╗ ██╔╝ ╚═══██╗   ██║           ║
║    ██║ ╚═╝ ██║██║██║ ╚═╝ ██║██║╚██████╗     ╚████╔╝ ██████╔╝██╗██║           ║
║    ╚═╝     ╚═╝╚═╝╚═╝     ╚═╝╚═╝ ╚═════╝      ╚═══╝  ╚═════╝ ╚═╝╚═╝           ║
║                                                                              ║
║                    BLOOMBERG-STYLE TRADING TERMINAL                          ║
║                            DEMO MODE                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║    Dashboard URL:  http://{args.host}:{args.port:<5}                                ║
║                                                                              ║
║    Features:                                                                 ║
║    • Real-time P&L tracking                                                  ║
║    • Position monitoring                                                     ║
║    • Whale signal tracker                                                    ║
║    • Risk dashboard with DDC status                                          ║
║    • Market maker LIP monitor                                                ║
║    • Trade blotter                                                           ║
║                                                                              ║
║    Press Ctrl+C to stop                                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    run_dashboard(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
