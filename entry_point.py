"""Standalone entry point for PyInstaller binary."""

import sys
import os

# Add src directory to path so we can import the package
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = sys._MEIPASS
    src_path = os.path.join(base_path, 'src')
else:
    # Running as script
    base_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(base_path, 'src')

sys.path.insert(0, src_path)

from somnia_contract_auditor.cli import main

if __name__ == "__main__":
    main()

