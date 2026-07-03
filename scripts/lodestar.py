#!/usr/bin/env python3
"""Dev convenience shim.

Runs the Lodestar CLI straight from a source checkout, without installing the
package. For a real install, install from the git URL (which bypasses the
package index) and call the `lodestar` command directly, e.g.
`pip install git+https://github.com/builder-seoro/lodestar` or
`uvx --from git+https://github.com/builder-seoro/lodestar lodestar --help`
(see the README). Do not install by the bare index name `lodestar` — it belongs
to an unrelated package on PyPI.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lodestar import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
