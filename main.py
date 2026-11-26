"""Publish the drawn broadsheet page: copy entry.png to the output directory.

The program checks the picture's header before it copies it: the PNG signature
and the IHDR width and height must pass, at most 1024 x 1024.

The file is written into $MAKEFUN_OUTPUT_DIR (default /output), the copied
bytes are hashed and the digest is checked against the source, so a truncated
or altered transfer fails loudly instead of shipping a broken picture.

It prints the source name and byte count, then "png: <width>x<height>" once
the header passes, then the copied size and digest.
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


def check_png(path):
    with open(path, "rb") as fh:
        head = fh.read(8)
        if head != b"\x89PNG\r\n\x1a\n":
            print("not a PNG: bad signature", file=sys.stderr)
            return None
        chunk = fh.read(16)
    if len(chunk) < 16:
        print("not a PNG: truncated IHDR chunk", file=sys.stderr)
        return None
    length = int.from_bytes(chunk[0:4], "big")
    ctype = chunk[4:8]
    width = int.from_bytes(chunk[8:12], "big")
    height = int.from_bytes(chunk[12:16], "big")
    if length != 13 or ctype != b"IHDR":
        print("not a PNG: no IHDR chunk at offset 8", file=sys.stderr)
        return None
    if width > 1024 or height > 1024:
        print("picture too large: %dx%d (limit 1024x1024)" % (width, height),
              file=sys.stderr)
        return None
    return width, height


def main():
    source_size = os.path.getsize(SOURCE)
    print("entry: %s %d bytes" % (NAME, source_size))
    if source_size >= 1048576:
        print("too large")
        return 1
    size_info = check_png(SOURCE)
    if size_info is None:
        return 1
    print("png: %dx%d" % size_info)
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
