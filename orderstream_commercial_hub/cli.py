import argparse
import json
import sys
from .license_gate import LicenseManager, LicenseTier
from .telemetry_hub import TelemetryHub
from .audit_certifier import AuditCertifier

def main():
    parser = argparse.ArgumentParser(
        prog="orderstream-hub",
        description="OrderStream Commercial Hub CLI: Licensing, Telemetry Sentinel & Enterprise Gateway"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Run the Commercial Hub FastAPI server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    # issue command
    issue_parser = subparsers.add_parser("issue", help="Issue an offline-verifiable license key")
    issue_parser.add_argument("--client", required=True, help="Client or organization name")
    issue_parser.add_argument("--tier", choices=["STARTER", "TEAM", "ENTERPRISE", "MA_AUDIT", "PRO"], default="STARTER")
    issue_parser.add_argument("--days", type=int, default=30, help="Validity duration in days")
    issue_parser.add_argument("--repos", type=int, default=None, help="Max repositories quota")
    issue_parser.add_argument("--tx", default="direct_wallet", help="Settlement transaction hash / Polar Order ID")

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a cryptographically signed license key")
    verify_parser.add_argument("--key", required=True, help="License key to verify")

    # pricing command
    subparsers.add_parser("pricing", help="Display OrderStream enterprise pricing matrix and wallets")

    # stats command
    subparsers.add_parser("stats", help="Show live telemetry and sentinel metrics")

    args = parser.parse_args()

    if args.command == "serve":
        try:
            import uvicorn
            from .server import app
            print(f"Starting OrderStream Commercial Hub on http://{args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("Error: uvicorn is not installed. Install via: pip install uvicorn", file=sys.stderr)
            sys.exit(1)

    elif args.command == "issue":
        mgr = LicenseManager()
        tier_enum = LicenseTier[args.tier]
        key = mgr.issue_license(
            client_name=args.client,
            tier=tier_enum,
            duration_days=args.days,
            max_repos=args.repos,
            payment_tx=args.tx
        )
        print(f"Issued License Key:\n{key}")
        print("\nDecoded Metadata:")
        print(json.dumps(mgr.verify_license(key), indent=2))

    elif args.command == "verify":
        mgr = LicenseManager()
        result = mgr.verify_license(args.key)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("valid") else 1)

    elif args.command == "pricing":
        from .server import get_pricing
        print(json.dumps(get_pricing(), indent=2))

    elif args.command == "stats":
        hub = TelemetryHub()
        print(json.dumps(hub.get_stats(), indent=2))

    else:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()
