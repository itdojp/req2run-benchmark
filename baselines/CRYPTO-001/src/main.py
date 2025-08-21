#!/usr/bin/env python3
"""Main entry point for the crypto tool."""

import sys
from cli import cli


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()