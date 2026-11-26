#!/usr/bin/env python3
"""Check the published entry.png and the repository around it.

Run from the repository root: python3 tools/check_entry.py
Prints one line per check and exits 0 when every check passes, 1 otherwise.
"""

import binascii
import os
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY = os.path.join(ROOT, "entry.png")
MAX_BYTES = 1048576
REQUIRED = ("entry.png", "main.py", "README.md")
PNG_SIG = b"\x89PNG\r\n\x1a\n"

failures = []


def report(ok, label, detail):
    print("%-22s %s  %s" % (label + ":", "ok  " if ok else "FAIL", detail))
    if not ok:
        failures.append(label)


def check_image():
    try:
        with Image.open(ENTRY) as im:
            size, mode = im.size, im.mode
    except Exception as exc:
        report(False, "image", "cannot open entry.png: %s" % exc)
        return
    ok = size[0] <= 1024 and size[1] <= 1024 and mode == "RGB"
    report(ok, "image", "%dx%d %s (need <=1024x1024 RGB)" % (size[0], size[1], mode))


def check_bytes():
    n = os.path.getsize(ENTRY)
    report(n <= MAX_BYTES, "bytes", "%d (limit %d)" % (n, MAX_BYTES))


def check_chunks():
    with open(ENTRY, "rb") as fh:
        data = fh.read()
    if data[:8] != PNG_SIG:
        report(False, "png chunks", "bad signature")
        return
    pos = 8
    seen_iend = False
    types = []
    while pos < len(data):
        if pos + 8 > len(data):
            report(False, "png chunks", "truncated chunk header at %d" % pos)
            return
        length = int.from_bytes(data[pos:pos + 4], "big")
        ctype = data[pos + 4:pos + 8]
        name = ctype.decode("latin-1")
        if not all(65 <= b <= 90 or 97 <= b <= 122 for b in ctype):
            report(False, "png chunks", "bad chunk type at %d: %r" % (pos, ctype))
            return
        end = pos + 8 + length + 4
        if end > len(data):
            report(False, "png chunks", "chunk %s length %d runs past end" % (name, length))
            return
        body = data[pos + 8:pos + 8 + length]
        crc = int.from_bytes(data[pos + 8 + length:end], "big")
        want = binascii.crc32(ctype + body) & 0xFFFFFFFF
        if crc != want:
            report(False, "png chunks", "bad CRC in %s: %08x != %08x" % (name, crc, want))
            return
        types.append(name)
        pos = end
        if name == "IEND":
            seen_iend = True
            break
    if not seen_iend:
        report(False, "png chunks", "no IEND")
        return
    if pos != len(data):
        report(False, "png chunks", "%d trailing bytes after IEND" % (len(data) - pos))
        return
    report(True, "png chunks", "%d chunks, CRCs valid, IEND at %d" % (len(types), pos))


def disk_files():
    return {p for p in os.listdir(ROOT) if os.path.isfile(os.path.join(ROOT, p))}


def git_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"],
                         capture_output=True, text=True, check=True).stdout
    return {line for line in out.splitlines() if line}


def check_files():
    on_disk = disk_files()
    try:
        in_git = git_files()
    except Exception as exc:
        report(False, "files", "git ls-files failed: %s" % exc)
        return
    print("%-22s %s" % ("files on disk:", " ".join(sorted(on_disk))))
    print("%-22s %s" % ("files in git:", " ".join(sorted(in_git))))
    missing_disk = [n for n in REQUIRED if n not in on_disk]
    missing_git = [n for n in REQUIRED if n not in in_git]
    ok = not missing_disk and not missing_git
    if ok:
        detail = "entry.png, main.py, README.md present in both"
    else:
        detail = "missing on disk: %s; missing in git: %s" % (
            ", ".join(missing_disk) or "-", ", ".join(missing_git) or "-")
    report(ok, "files", detail)


def check_copy():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, MAKEFUN_OUTPUT_DIR=tmp)
        proc = subprocess.run([sys.executable, "main.py"], cwd=ROOT, env=env,
                              capture_output=True, text=True)
        copied = os.path.join(tmp, "entry.png")
        if proc.returncode != 0:
            report(False, "main.py copy", "main.py exited %d" % proc.returncode)
            return
        if not os.path.isfile(copied):
            report(False, "main.py copy", "no entry.png written to output dir")
            return
        with open(copied, "rb") as a, open(ENTRY, "rb") as b:
            ok = a.read() == b.read()
        report(ok, "main.py copy", "output identical" if ok else "output differs from entry.png")


def main():
    check_image()
    check_bytes()
    check_chunks()
    check_files()
    check_copy()
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
