"""Entry point for ``python -m app.seed``."""

import sys

from app.seed.cli import main

if __name__ == "__main__":
    sys.exit(main())
