"""
deb_extractor.py — Extracts .deb (ar-format) archives, including data.tar.
"""

import io
import os
import sys
import tarfile


class DebExtractor:
    _GLOBAL_MAGIC = b"!<arch>\n"
    _ENTRY_SIZE = 60

    @staticmethod
    def extract(deb_path: str, outdir: str) -> None:
        DebExtractor._extract_manual(deb_path, outdir)

    @staticmethod
    def _extract_manual(deb_path: str, outdir: str) -> None:
        with open(deb_path, "rb") as f:
            if f.read(8) != DebExtractor._GLOBAL_MAGIC:
                sys.exit("[-] Not a valid .deb (ar) archive.")
            while True:
                header = f.read(DebExtractor._ENTRY_SIZE)
                if len(header) < DebExtractor._ENTRY_SIZE:
                    break
                name = header[0:16].rstrip().decode("ascii", errors="replace").rstrip("/")
                size = int(header[48:58].strip())
                data = f.read(size)
                if size % 2:
                    f.read(1)
                if name.startswith("data.tar"):
                    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
                        tf.extractall(outdir)
                    return
        sys.exit("[-] Data.tar not found inside .deb.")
