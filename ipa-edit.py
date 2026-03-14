"""
iPA-Edit — Sign and tweak iOS IPA files.

Features:
  - Inject tweaks into iPA
  - Remove injected tweaks
  - Export tweaks from iPA
  - Sign iPA with certificate

Usage:
  python ipa-edit.py                          # interactive menu
  python ipa-edit.py -i app.ipa [options...]  # CLI mode

Version: v1.3
Author [Remake]: SHAJON-404
GitHub: https://github.com/SHAJON-404
Website: https://shajon.dev
License: GPLv3
"""

import sys
import argparse

from modules.__ipa_editor import IPAEditor
from modules.__menu import main_menu_loop

__version__ = "1.3"


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    p = argparse.ArgumentParser(description="iPA Edit – sign and tweak iPA files.")
    p.add_argument("-i",                         type=str,            help="input .ipa")
    p.add_argument("-o",                         type=str,            help="output path/name")
    p.add_argument("-tw",                        action="store_true", help="inject tweaks from tweaks/ folder")
    p.add_argument("-rm-tw",   dest="rm_tw",     type=str,            help="remove tweaks (comma-separated names)")
    p.add_argument("-d", "--export-tweaks", dest="export_tw", action="store_true",
                   help="export .dylib/.framework tweaks from iPA to tweaks_extracted/")
    return p


if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            main_menu_loop()
        else:
            ns = build_parser().parse_args()
            if not ns.i:
                print("[-] Error: Input iPA (-i) is required when using command-line arguments.")
                sys.exit(1)

            # Strip stray quotes and slashes from path arguments
            for attr in ("i", "o"):
                val = getattr(ns, attr, None)
                if isinstance(val, str):
                    setattr(ns, attr, val.strip(' "\'').rstrip("/\\"))

            IPAEditor(ns).run()

    except KeyboardInterrupt:
        print("\n[*] Interrupted, exiting.")
        sys.exit(0)