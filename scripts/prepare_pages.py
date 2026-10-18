"""Stage the static website without repository-only teaching documents."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"teacher", "scripts", "tests", ".git", ".github", "__pycache__", ".pytest_cache"}


def prepare(source: Path, destination: Path) -> None:
    source, destination = source.resolve(), destination.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError("Use a staging directory outside the repository")
    if destination.exists():
        raise FileExistsError(f"Staging directory already exists: {destination}")
    # Do not follow a symlink that could reintroduce excluded repository files.
    def ignore(directory, names):
        return [name for name in names if name in EXCLUDED
                or (Path(directory) / name).is_symlink()]
    shutil.copytree(source, destination, ignore=ignore)
    assert not (destination / "teacher").exists()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(ROOT, args.output)
    print(f"Pages staged without teacher/: {args.output}")
