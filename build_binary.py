"""Build script for creating a standalone binary using PyInstaller."""

import subprocess
import sys
import os
from pathlib import Path


def build_binary():
    """Build a standalone binary using PyInstaller."""
    project_root = Path(__file__).parent
    spec_file = project_root / "somnia-auditor.spec"
    
    # Check if spec file exists, otherwise use command line options
    if spec_file.exists():
        cmd = ["pyinstaller", "--clean", str(spec_file)]
        print("Building binary with PyInstaller using spec file...")
    else:
        src_dir = project_root / "src"
        entry_point = project_root / "entry_point.py"
        
        if not entry_point.exists():
            print("Error: entry_point.py not found. Please ensure it exists.")
            return 1
        
        cmd = [
            "pyinstaller",
            "--name=somnia-auditor",
            "--onefile",
            "--console",
            "--clean",
            "--hidden-import=click",
            "--hidden-import=somnia_contract_auditor",
            "--hidden-import=somnia_contract_auditor.cli",
            "--hidden-import=somnia_contract_auditor.file_discovery",
            "--hidden-import=somnia_contract_auditor.slither_runner",
            "--hidden-import=somnia_contract_auditor.solhint_runner",
            "--hidden-import=somnia_contract_auditor.report_generator",
            f"--paths={src_dir}",
            str(entry_point),
        ]
        print("Building binary with PyInstaller...")
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=project_root)
        print("\n✓ Binary built successfully!")
        
        # Determine binary name based on OS
        if os.name == 'nt':
            binary_name = "somnia-auditor.exe"
        else:
            binary_name = "somnia-auditor"
        
        binary_path = project_root / "dist" / binary_name
        if binary_path.exists():
            file_size = binary_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"✓ Output location: {binary_path}")
            print(f"✓ Binary size: {file_size:.2f} MB")
        else:
            print(f"⚠ Warning: Expected binary not found at {binary_path}")
            print(f"  Checking dist directory...")
            dist_files = list((project_root / "dist").glob("*"))
            if dist_files:
                print(f"  Found files: {[f.name for f in dist_files]}")
        
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
        return e.returncode
    except FileNotFoundError:
        print("\n✗ PyInstaller not found. Please install it:")
        print("  pip install pyinstaller")
        return 1


if __name__ == "__main__":
    sys.exit(build_binary())

