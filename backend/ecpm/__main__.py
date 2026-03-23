"""CLI entry point for ECPM: python -m ecpm."""

import argparse
import sys


def main() -> None:
    """Parse CLI arguments and dispatch subcommands."""
    parser = argparse.ArgumentParser(
        prog="ecpm",
        description="Economic Crisis Prediction Model CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # fetch subcommand
    fetch_parser = subparsers.add_parser("fetch", help="Trigger data fetch")
    fetch_parser.add_argument(
        "--series",
        type=str,
        default=None,
        help="Specific series ID to fetch (default: all)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "fetch":
        print("Not implemented yet")
        sys.exit(0)


if __name__ == "__main__":
    main()
