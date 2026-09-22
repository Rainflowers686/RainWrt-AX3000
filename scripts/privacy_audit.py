#!/usr/bin/env python3
"""Fail-closed pattern inventory. Emits paths/types/object IDs, never values.

A zero result is not proof that arbitrary credentials cannot exist.
--all-history includes every local ref, including quarantined legacy.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = '4fc16f2985a358bd43bb522e43f05395fcbd6ed5'
RULES = {
    'private_context': re.compile(rb'ouc-net|ouc-portal|xha[.]ouc[.]edu[.]cn|100[.]69[.]|/etc/ouc-|private-router-backups', re.I),
    'private_key_block': re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/=]{32}'),
    'credential_token': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16})'),
    'wireguard_secret': re.compile(rb'(?im)^\s*(?:PrivateKey|PresharedKey)\s*=\s*[A-Za-z0-9+/]{43}='),
}
DUMP = re.compile(r'(^|/)(mtd\d+\.(bin|dump)|sysupgrade-backup[^/]*\.(tgz|gz|tar))$')
# Context rules in policy are informational; secret rules NEVER exempt files.
POLICY = {'scripts/privacy_audit.py', 'scripts/audit-public-release.sh', 'docs/PUBLIC_RELEASE_AUDIT.md'}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--all-history', action='store_true')
    p.add_argument('--rootfs', type=pathlib.Path)
    args = p.parse_args()
    findings, scanned, seen = [], 0, set()

    def scan(data, path, scope, obj=''):
        nonlocal scanned
        scanned += 1
        types = [name for name, rule in RULES.items() if rule.search(data)]
        if DUMP.search(path):
            types.append('backup_filename')
        for kind in types:
            classification = 'policy_text' if kind == 'private_context' and path in POLICY else 'REVIEW_REQUIRED'
            findings.append({'scope': scope, 'path': path, 'object': obj,
                             'type': kind, 'classification': classification})
    for raw in git('ls-files', '-z').split(b'\0'):
        if not raw:
            continue
        name = raw.decode()
        path = ROOT / name
        if path.is_symlink():
            scan(str(path.readlink()).encode(), name, 'tracked_symlink')
        elif path.is_file():
            scan(path.read_bytes(), name, 'tracked')
        else:
            raise RuntimeError('tracked path missing')
    objects = git('rev-list', '--objects', *(['--all'] if args.all_history else [BASE + '..HEAD'])).splitlines()
    proc = subprocess.Popen(['git', '-C', str(ROOT), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for line in objects:
            fields = line.split(b' ', 1)
            oid = fields[0].decode()
            if oid in seen:
                continue
            seen.add(oid)
            proc.stdin.write((oid + '\n').encode())
            proc.stdin.flush()
            header = proc.stdout.readline().split()
            if len(header) != 3:
                raise RuntimeError('git object unreadable')
            size = int(header[2])
            data = proc.stdout.read(size)
            if len(data) != size or proc.stdout.read(1) != b'\n':
                raise RuntimeError('short git object')
            if header[1] == b'blob':
                path = fields[1].decode(errors='replace') if len(fields) > 1 else '(unknown path)'
                scan(data, path, 'history', oid)
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError('git object scan failed')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    if args.rootfs:
        if not args.rootfs.is_dir():
            raise RuntimeError('rootfs missing')
        for path in sorted(args.rootfs.rglob('*')):
            if path.is_file() and not path.is_symlink():
                scan(path.read_bytes(), path.relative_to(args.rootfs).as_posix(), 'rootfs')
    blocked = any(x['classification'] == 'REVIEW_REQUIRED' for x in findings)
    print(json.dumps({'status': 'REVIEW_REQUIRED' if blocked else 'PATTERN_SCAN_PASS',
                      'scope': 'all_local_refs' if args.all_history else 'public_branch_delta',
                      'files_blobs_scanned': scanned, 'findings': findings,
                      'limitations': 'Pattern scan is not a secret absence guarantee; opaque archives must never be released.'}, indent=2))
    return 1 if blocked else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print('{"status":"SCAN_ERROR","release_gate":"BLOCKED"}')
        sys.exit(2)
