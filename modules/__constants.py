"""
constants.py — Shared constants for iPA-Edit.
"""

import os

# ANSI Colors
RED   = "\033[91m"
GREEN = "\033[92m"
WHITE = "\033[97m"
RESET = "\033[0m"

# Visual separator
SEP = f"{WHITE}{'-' * 80}{RESET}"

# Directory of the top-level ipa-edit.py script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__ if False else
    os.path.join(os.path.dirname(__file__), "..", "ipa-edit.py")))
