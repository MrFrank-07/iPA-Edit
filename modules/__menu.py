"""
menus.py — Interactive CLI menus for iPA-Edit.

Contains the main menu loop and per-feature sub-menus.
"""

import os
import sys
import time
import zipfile
import argparse
import platform

from .__constants import RED, GREEN, WHITE, RESET, SEP
from .__ipa_editor import IPAEditor


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def show_main_menu() -> int:
    """Display the main interactive menu and return the user's choice."""
    print(SEP)
    print(f"{WHITE}                    iPA Edit - By S. SHAJON{RESET}")
    print(SEP)
    print(f"{WHITE}1.{RESET} Inject tweaks")
    print(f"{WHITE}2.{RESET} Remove tweaks")
    print(f"{WHITE}3.{RESET} Export tweaks from iPA")
    print(f"{WHITE}4.{RESET} Sign IPA with certificate")
    print(f"{WHITE}5.{RESET} Exit")
    print(SEP)

    try:
        choice = input(f"{WHITE}[?] Select option (1-5): {RESET}").strip()
        return int(choice)
    except ValueError:
        return 0


def main_menu_loop() -> None:
    """Entry point for the interactive session."""
    while True:
        os.system("cls" if platform.system() == "Windows" else "clear")
        try:
            choice = show_main_menu()

            if choice == 1:
                ns = add_tweaks_menu()
                if ns:
                    editor = IPAEditor(ns)
                    editor.run()
                    editor._remove_temp()
                    input(f"\n{WHITE}[*] Press ENTER to return to main menu...{RESET}")

            elif choice == 2:
                ns = remove_tweaks_menu()
                if ns:
                    editor = IPAEditor(ns)
                    editor.run()
                    editor._remove_temp()
                    input(f"\n{WHITE}[*] Press ENTER to return to main menu...{RESET}")

            elif choice == 3:
                ns = export_tweaks_menu()
                if ns:
                    editor = IPAEditor(ns)
                    editor.run()
                    editor._remove_temp()
                    input(f"\n{WHITE}[*] Press ENTER to return to main menu...{RESET}")

            elif choice == 4:
                editor = IPAEditor(argparse.Namespace())
                editor.sign_existing_ipa()
                editor._remove_temp()
                input(f"\n{WHITE}[*] Press ENTER to return to main menu...{RESET}")

            elif choice == 5:
                print(f"{WHITE}[*] Exiting...{RESET}")
                sys.exit(0)

            else:
                print(f"{RED}[-] Invalid option{RESET}")
                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n{WHITE}[*] Interrupted, exiting.{RESET}")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Sub-menus
# ---------------------------------------------------------------------------

def _default_ns() -> argparse.Namespace:
    """Return an argparse Namespace with all IPA-Edit flags at their defaults."""
    ns = argparse.Namespace()
    defaults = {
        "i": None, "o": None,
        "tw": False, "rm_tw": None, "export_tw": False,
    }
    for k, v in defaults.items():
        setattr(ns, k, v)
    return ns



def add_tweaks_menu() -> argparse.Namespace | None:
    """Interactive sub-menu for tweak injection."""
    ns    = _default_ns()
    ns.tw = True

    print(SEP)
    print(f"{WHITE}[*] Tweak Injection Mode{RESET}")
    print(SEP)

    while not ns.i:
        path = input(f"{WHITE}[?] Input IPA path: {RESET}").strip(' "\'')
        if path and os.path.isfile(path):
            ns.i = path
        elif path:
            print(f"{RED}[-] File not found: {path}{RESET}")
        else:
            return None

    ns.o = input(f"{WHITE}[?] Output path (leave empty for auto): {RESET}").strip(' "\'') or None
    return ns


def remove_tweaks_menu() -> argparse.Namespace | None:
    """Interactive sub-menu for tweak removal."""
    ns = _default_ns()

    print(SEP)
    print(f"{WHITE}[*] Tweak Removal Mode{RESET}")
    print(SEP)

    while not ns.i:
        path = input(f"{WHITE}[?] Input IPA path: {RESET}").strip(' "\'')
        if path and os.path.isfile(path):
            ns.i = path
        elif path:
            print(f"{RED}[-] File not found: {path}{RESET}")
        else:
            return None

    ns.o = input(f"{WHITE}[?] Output path (leave empty for auto): {RESET}").strip(' "\'') or None
    print(SEP)

    print(f"{WHITE}[*] Scanning IPA for injected tweaks...{RESET}")
    try:
        available_tweaks: list[str] = []
        with zipfile.ZipFile(ns.i, "r") as zf:
            app_folder_name = None
            for entry in zf.namelist():
                parts = entry.replace("\\", "/").split("/")
                if len(parts) >= 2 and parts[0] == "Payload" and parts[1].endswith(".app"):
                    app_folder_name = parts[1]
                    break

            if app_folder_name:
                fw_prefix  = f"Payload/{app_folder_name}/Frameworks/"
                tweak_set: set[str] = set()
                for entry in zf.namelist():
                    normalized = entry.replace("\\", "/")
                    if normalized.startswith(fw_prefix) and len(normalized) > len(fw_prefix):
                        file_name = normalized[len(fw_prefix):].split("/")[0]
                        if file_name.endswith(".dylib") or file_name.endswith(".framework"):
                            tweak_set.add(file_name)
                available_tweaks = sorted(tweak_set)

    except Exception as e:
        print(f"{RED}[-] Failed to read IPA: {e}{RESET}")
        return None

    if not available_tweaks:
        print(f"{RED}[-] No tweaks (.dylib or .framework) found in the IPA.{RESET}")
        return None

    print(f"{WHITE}[*] Injected tweaks:{RESET}")
    for i, twk in enumerate(available_tweaks, 1):
        print(f"  {i}: {twk}")
    print(SEP)

    print("[?] use , for multiple  |  'all' for every tweak  |  'exit' to cancel")
    selection = input("[?] Tweak number(s) to remove: ").strip().lower()

    if selection == "exit":
        print(f"{WHITE}[*] Cancelled{RESET}")
        return None

    if selection == "all":
        ns.rm_tw = ",".join(available_tweaks)
    else:
        try:
            chosen   = [available_tweaks[int(n.strip()) - 1] for n in selection.split(",")]
            ns.rm_tw = ",".join(chosen)
        except (ValueError, IndexError):
            print(f"{RED}[-] Invalid selection.{RESET}")
            return None

    return ns


def export_tweaks_menu() -> argparse.Namespace | None:
    """Interactive sub-menu for exporting tweaks."""
    ns = _default_ns()
    ns.export_tw = True

    print(SEP)
    print(f"{WHITE}[*] Tweak Export Mode{RESET}")
    print(SEP)

    while not ns.i:
        path = input(f"{WHITE}[?] Input IPA path: {RESET}").strip(' "\'')
        if path and os.path.isfile(path):
            ns.i = path
        elif path:
            print(f"{RED}[-] File not found: {path}{RESET}")
        else:
            return None

    # No specific output path needed for export; it uses tweaks_extracted/
    return ns

