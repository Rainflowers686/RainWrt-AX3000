#!/usr/bin/env python3
"""Validate and stage locally supplied CR8808 board-data inputs.

The board-data files are intentionally not redistributed by RainWrt. This
script only accepts exact, locally supplied inputs and copies them into the
ephemeral ipq-wifi package build directory.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "vendor-local" / "board-data"
EXPECTED = {
    "board-redmi_ax3000.ipq5018": "a1d03029566e469ceee4d570324dfa015f3d01e351bc87c81329ffdd7a7c4186",
    "board-redmi_ax3000.qcn6122": "91c689226aa5a3af853063452393055c5e764866fec707ccd504738314e75134",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(source_dir: pathlib.Path, expected: dict[str, str] = EXPECTED) -> dict[str, pathlib.Path]:
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise ValueError(f"local board-data directory is missing or not a real directory: {source_dir}")
    entries = list(source_dir.iterdir())
    unexpected = sorted(entry.name for entry in entries if entry.name not in expected)
    if unexpected:
        raise ValueError("unexpected entries in local board-data directory")

    result: dict[str, pathlib.Path] = {}
    for name, required_hash in expected.items():
        path = source_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"required local board-data file is missing or not a regular file: {name}")
        actual_hash = sha256(path)
        if actual_hash != required_hash:
            raise ValueError(f"SHA256 mismatch for {name}: expected {required_hash}, got {actual_hash}")
        result[name] = path
    return result


def stage(source_dir: pathlib.Path, dest_dir: pathlib.Path,
          expected: dict[str, str] = EXPECTED) -> None:
    files = validate(source_dir, expected)
    if dest_dir.is_symlink() or not dest_dir.is_dir():
        raise ValueError(f"package staging directory is missing or not a real directory: {dest_dir}")
    # Validate every existing destination before writing anything.
    for name, required_hash in expected.items():
        destination = dest_dir / name
        if destination.is_symlink():
            raise ValueError(f"refusing symlink in package staging directory: {name}")
        if destination.exists():
            if not destination.is_file() or sha256(destination) != required_hash:
                raise ValueError(f"conflicting board-data already exists in package staging directory: {name}")
    for name, source in files.items():
        destination = dest_dir / name
        if not destination.exists():
            shutil.copyfile(source, destination)
        if sha256(destination) != expected[name]:
            raise ValueError(f"staged board-data failed SHA256 verification: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check", help="validate local CR8808 board-data")
    check_parser.add_argument("--source-dir", type=pathlib.Path, default=DEFAULT_SOURCE)
    stage_parser = subparsers.add_parser("stage", help="validate and inject into package build staging")
    stage_parser.add_argument("--source-dir", type=pathlib.Path, default=DEFAULT_SOURCE)
    stage_parser.add_argument("--dest-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "check":
            validate(args.source_dir)
        else:
            stage(args.source_dir, args.dest_dir)
    except (OSError, ValueError) as exc:
        required_inputs_missing = (
            args.command == "check"
            and args.source_dir.is_dir()
            and any(not (args.source_dir / name).exists() for name in EXPECTED)
        )
        if args.command == "check" and (not args.source_dir.exists() or required_inputs_missing):
            print("Required local board-data files are missing.", file=sys.stderr)
            print("RainWrt does not redistribute these files because redistribution permission has not been established.", file=sys.stderr)
            print(f"Place the legally obtained files in: {args.source_dir}", file=sys.stderr)
            for name, digest in EXPECTED.items():
                print(f"  {name}  SHA256 {digest}", file=sys.stderr)
        else:
            print(f"Local board-data validation failed: {exc}", file=sys.stderr)
        return 1
    for name, digest in EXPECTED.items():
        print(f"LOCAL_BDF_PASS {name} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
