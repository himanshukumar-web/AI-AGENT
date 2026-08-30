"""
JARVIS AI — Root Application Launcher
Allows starting JARVIS directly from project root.

Usage:
    python main.py
    python main.py --cli
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from MAIN.main import main

if __name__ == "__main__":
    main()
