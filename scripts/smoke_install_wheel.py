"""Install the built wheel into a fresh venv and import the public SDK surface."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def _one_wheel(dist_dir: Path) -> Path:
    matches = sorted(dist_dir.glob("*.whl"))
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one wheel artifact, found {len(matches)}.")
    return matches[0]


def _venv_python(venv_dir: Path) -> Path:
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    return venv_dir / bin_dir / "python"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist_dir", type=Path)
    args = parser.parse_args()

    wheel = _one_wheel(args.dist_dir)
    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        python = _venv_python(venv_dir)

        subprocess.run(
            [str(python), "-m", "pip", "install", str(wheel)],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-c",
                (
                    "import zenture; "
                    "from zenture import AsyncZenture, Zenture; "
                    "assert zenture.__version__; "
                    "assert Zenture.__name__ == 'Zenture'; "
                    "assert AsyncZenture.__name__ == 'AsyncZenture'"
                ),
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
