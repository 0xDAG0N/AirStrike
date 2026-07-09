#!/usr/bin/env python3
"""AirStrike entry-point shim.

Kept so the documented ``sudo python run.py`` keeps working. All logic lives in
``app.cli.main`` (also exposed as the ``airstrike`` console script), so the two launch
paths share exactly one implementation.
"""

from app.cli import main

if __name__ == "__main__":
    main()
