#!/usr/bin/env python3
"""flock helper for PaperDesk (Node has no flock; the app shells out here).

Usage:
  opslock.py probe <lockfile>          -> prints HELD or FREE, exit 0
  opslock.py hold   <lockfile> <cmd>…  -> takes LOCK_EX|LOCK_NB, holds it for
                                          the child's lifetime; exits 3 with
                                          {"blocked":"SINGLE_INSTANCE"} if
                                          the lock is already held.
"""
import fcntl
import json
import os
import subprocess
import sys


def probe(path: str) -> int:
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        print("FREE")
    except OSError:
        print("HELD")
    finally:
        os.close(fd)
    return 0


def hold(path: str, cmd) -> int:
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(json.dumps({"blocked": "SINGLE_INSTANCE",
                          "detail": f"lock held: {path}"}))
        return 3
    try:
        return subprocess.call(cmd)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "probe":
        sys.exit(probe(sys.argv[2]))
    if len(sys.argv) >= 4 and sys.argv[1] == "hold":
        sys.exit(hold(sys.argv[2], sys.argv[3:]))
    print("usage: opslock.py probe|hold ...", file=sys.stderr)
    sys.exit(2)
