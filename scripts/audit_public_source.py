#!/usr/bin/env python3
"""Audit exact proposed public refs for restricted board-data blobs and secrets."""
import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESTRICTED_BLOBS = {
    "5b87f35cb94713c340acb14ea90b1f9ffcfe67e9": "CR8808-IPQ5018",
    "2489f93c64f40ab7167616e50b2159d40045ebb0": "CR8808-QCN6122",
    "e3965aec875068bb289175e9aa38ee91b82195bc": "CR880X-reference-IPQ5018",
    "be5a19dd2bd91d952effb2a577c7b094f98939c3": "CR880X-reference-QCN6122",
}
RESTRICTED_PATHS = (
    "package/firmware/ipq-wifi/src/board-redmi_ax3000.ipq5018",
    "package/firmware/ipq-wifi/src/board-redmi_ax3000.qcn6122",
    "package/firmware/ipq-wifi/src/board-xiaomi_cr880x.ipq5018",
    "package/firmware/ipq-wifi/src/board-xiaomi_cr880x.qcn6122",
)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", action="append", default=[], required=True,
                        help="exact public ref to scan; repeat to scan multiple refs")
    args = parser.parse_args()
    objects = set(git("rev-list", "--objects", "--no-object-names", *args.ref).splitlines())
    reachable = {oid: label for oid, label in RESTRICTED_BLOBS.items() if oid in objects}
    tracked = set(git("ls-files").splitlines())
    tracked_local_paths = sorted(path for path in tracked if path.startswith("vendor-local/board-data/"))
    working_paths = [path for path in RESTRICTED_PATHS if (ROOT / path).exists()]
    tracked_paths = [path for path in RESTRICTED_PATHS if path in tracked]
    ref_paths = {}
    for ref in args.ref:
        names = set(git("ls-tree", "-r", "--name-only", ref).splitlines())
        found = sorted(names.intersection(RESTRICTED_PATHS))
        if found:
            ref_paths[ref] = found
    local_files_not_ignored = []
    for name in (
        "board-redmi_ax3000.ipq5018",
        "board-redmi_ax3000.qcn6122",
    ):
        rel = f"vendor-local/board-data/{name}"
        result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "-q", rel])
        if result.returncode != 0:
            local_files_not_ignored.append(rel)
    privacy = subprocess.run(
        [sys.executable, str(ROOT / "scripts/privacy_audit.py"),
         *sum((["--ref", ref] for ref in args.ref), [])],
        check=False, text=True, capture_output=True)
    try:
        privacy_result = json.loads(privacy.stdout)
    except json.JSONDecodeError:
        privacy_result = {"status": "SCAN_ERROR"}
    passed = not (reachable or working_paths or tracked_paths or tracked_local_paths or ref_paths or
                  local_files_not_ignored or privacy.returncode != 0 or
                  privacy_result.get("status") != "PATTERN_SCAN_PASS")
    result = {
        "status": "PUBLIC_SOURCE_AUDIT_PASS" if passed else "PUBLIC_SOURCE_AUDIT_FAIL",
        "refs": args.ref,
        "restricted_blob_objects_reachable": reachable,
        "restricted_paths_in_working_tree": working_paths,
        "restricted_paths_tracked": tracked_paths,
        "local_board_data_paths_tracked": tracked_local_paths,
        "restricted_paths_by_ref": ref_paths,
        "local_board_data_ignore_rules": "PASS" if not local_files_not_ignored else "FAIL",
        "local_paths_not_ignored": local_files_not_ignored,
        "privacy_pattern_scan": privacy_result.get("status"),
        "privacy_pattern_findings": privacy_result.get("findings", []),
        "binary_firmware_release": "BLOCKED_BY_BDF_REDISTRIBUTION",
    }
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "PUBLIC_SOURCE_AUDIT_ERROR", "error": type(exc).__name__}))
        raise SystemExit(2)
