"""Publish the drawn broadsheet page: copy entry.png to the output directory.

The file is written into $MAKEFUN_OUTPUT_DIR (default /output), the copied
bytes are hashed and the digest is checked against the source, so a truncated
or altered transfer fails loudly instead of shipping a broken picture.
"""

import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
NAME = os.path.basename(SOURCE)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    source_size = os.path.getsize(SOURCE)
    print("entry: %s %d bytes" % (NAME, source_size))
    if source_size >= 1048576:
        print("too large")
        return 1
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, NAME)
    shutil.copyfile(SOURCE, target)
    size = os.path.getsize(target)
    copied = digest(target)
    print(size)
    print(copied)
    if copied != digest(SOURCE):
        print("sha256 mismatch", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
