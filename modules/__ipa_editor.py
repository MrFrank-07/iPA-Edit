"""
ipa_editor.py — Core IPAEditor class for iPA-Edit.

Handles tweak injection, removal, export, and code signing.
"""

import os
import sys
import time
import atexit
import shutil
import zipfile
import platform
import argparse
import subprocess

from .__constants import RED, GREEN, WHITE, RESET, SEP
from . import __tweak_manager as tweak_manager


class IPAEditor:
    """
    Main controller for IPA operations.
    Handles tweak injection, removal, export, and code signing.
    """

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize the editor with parsed command-line arguments."""
        self.args         = args
        self.script_dir   = _get_script_dir()
        self.temp_dir     = os.path.join(self.script_dir, ".temp")
        self.app_path:     str | None = None
        self.zip_path:     str | None = None
        self.payload_path: str | None = None
        self.ipa_path:     str | None = None
        self._register_cleanup()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_zsign(self) -> str:
        """Locate the platform-specific zsign binary."""
        platform_map = {
            "Windows": "windows/zsign.exe",
            "Darwin":  "mac/zsign",
            "Linux":   "linux/zsign",
        }
        local = os.path.join(self.script_dir, "zsign", platform_map.get(platform.system(), ""))
        if os.path.isfile(local):
            return local
        if shutil.which("zsign"):
            return "zsign"
        return input(f"{WHITE}[?] Zsign path not found. Enter manually: {RESET}").strip(' "\'')

    def _resolve_certificate(self) -> tuple[str, str]:
        """Automatically detect or prompt for code signing credentials."""
        cert_dir = os.path.join(self.script_dir, "certificate")
        p12 = mp = ""
        if os.path.isdir(cert_dir):
            for f in os.listdir(cert_dir):
                if f.endswith(".p12"):
                    p12 = os.path.join(cert_dir, f)
                elif f.endswith(".mobileprovision"):
                    mp = os.path.join(cert_dir, f)

        if not p12:
            p12 = input(f"{WHITE}[?] .p12 path: {RESET}").strip(" \"'")
        if not mp:
            mp = input(f"{WHITE}[?] .mobileprovision path: {RESET}").strip(" \"'")

        if p12 and mp:
            print(f"{GREEN}[+] Cert: {os.path.basename(p12)} + {os.path.basename(mp)}{RESET}")
            return p12, mp
        return "", ""

    def _get_auto_out_path(self, suffix: str) -> str:
        base_name = os.path.basename(self.args.i) if getattr(self.args, "i", None) else "output"
        if base_name.lower().endswith(".ipa"):
            base_name = base_name[:-4]

        folder_name = "Unsigned" if "unsigned" in suffix.lower() else "Signed"
        folder_path = os.path.join(self.script_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return os.path.join(folder_path, f"{base_name}_{suffix}.ipa")

    def _register_cleanup(self) -> None:
        atexit.register(self._remove_temp)

    def _remove_temp(self) -> None:
        if not os.path.isdir(self.temp_dir):
            return
        if os.path.abspath(os.getcwd()).startswith(os.path.abspath(self.temp_dir)):
            os.chdir(self.script_dir)
        for _ in range(3):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"{WHITE}[*] Cleaned up .temp folder{RESET}")
                return
            except (PermissionError, OSError):
                time.sleep(0.5)

    def _ensure_temp(self) -> str:
        os.makedirs(self.temp_dir, exist_ok=True)
        return self.temp_dir

    # ------------------------------------------------------------------
    # Main execution entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Orchestrate tweak injection, removal, or export.
        """
        self.ipa_path = self.args.i

        if getattr(self.args, "export_tw", False):
            tweak_manager.export_tweaks(self)

        if getattr(self.args, "tw", False):
            tweak_manager.add_tweaks(self)

        if getattr(self.args, "rm_tw", None):
            tweak_manager.remove_tweaks(self)

        print(SEP)
        print(f"{GREEN}[+] Execution finished.{RESET}")
        print(SEP)

    # ------------------------------------------------------------------
    # IPA archive operations
    # ------------------------------------------------------------------

    def _unzip_ipa(self, ipa_path: str) -> tuple[str, str, str]:
        print(SEP)
        print(f"{WHITE}[*] Extracting iPA{RESET}")
        temp     = self._ensure_temp()
        zip_path = os.path.join(temp, os.path.basename(ipa_path).replace(".ipa", ".zip"))
        shutil.copy2(ipa_path, zip_path)

        if not os.path.exists(zip_path):
            sys.exit("[-] .ipa file could not be found.")

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp)

        payload_path = os.path.join(temp, "Payload")
        app_folder   = next((i for i in os.listdir(payload_path) if i.endswith(".app")), None)
        if app_folder is None:
            sys.exit("[-] .app folder not found inside iPA.")

        print(f"{GREEN}[+] Extracted iPA{RESET}")
        return os.path.join(payload_path, app_folder), zip_path, payload_path

    # ------------------------------------------------------------------
    # Standalone sign mode
    # ------------------------------------------------------------------

    def sign_existing_ipa(self) -> None:
        """
        Interactive process to sign an existing IPA file with zsign.
        """
        print(SEP)
        print(f"{WHITE}[*] Sign IPA Mode{RESET}")
        print(SEP)

        ipa_path = input(f"{WHITE}[?] Input IPA path: {RESET}").strip(' "\'')
        if not ipa_path or not os.path.isfile(ipa_path):
            print(f"{RED}[-] Invalid IPA path. Please provide a valid file.{RESET}")
            return

        p12_path, mp_path = self._resolve_certificate()
        if not p12_path or not mp_path:
            print(f"{RED}[-] Certificate or Mobile Provision missing.{RESET}")
            return

        cert_pw  = input(f"{WHITE}[?] Certificate password: {RESET}")
        out_path = input(f"{WHITE}[?] Output path (leave empty for auto): {RESET}").strip(' "\'') or None
        zsign    = self._resolve_zsign()
        if not zsign:
            print(f"{RED}[-] zsign tool not found. Signing aborted.{RESET}")
            return

        if not out_path:
            base_name  = os.path.basename(ipa_path).replace(".ipa", "")
            signed_dir = os.path.join(self.script_dir, "Signed")
            os.makedirs(signed_dir, exist_ok=True)
            out_path   = os.path.join(signed_dir, f"{base_name}_signed.ipa")

        print(f"\n{WHITE}[*] Initiating code signing...{RESET}")
        cmd    = f'"{zsign}" -k "{p12_path}" -m "{mp_path}" -p "{cert_pw}" -o "{out_path}" -z 9 "{ipa_path}"'
        result = subprocess.run(cmd, shell=True)

        if result.returncode == 0 and os.path.isfile(out_path):
            print(f"{GREEN}[+] Signature applied successfully: {out_path}{RESET}")
        else:
            print(f"{RED}[-] Code signing process failed.{RESET}")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _get_script_dir() -> str:
    """Return the root project directory (parent of modules/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
