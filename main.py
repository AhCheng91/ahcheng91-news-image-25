"""Ship the finished front page to the output folder and verify it.

entry.png beside this script is copied into $MAKEFUN_OUTPUT_DIR (created on
demand, /output when the variable is unset). The bytes that landed are hashed
and the digest must match the original, so a partial or corrupted copy is
reported as a failure rather than silently published.
"""

import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    name = os.path.basename(SRC)
    size = os.path.getsize(SRC)
    print("entry: %s %d bytes" % (name, size))
    if size >= 1048576:
        print("too large")
        return 1
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, name)
    shutil.copyfile(SRC, dst)
    print("size", os.path.getsize(dst))
    print("sha256", sha(dst))
    if sha(dst) != sha(SRC):
        print("copy does not match the source")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
