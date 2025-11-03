"""Solhint analysis runner module."""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any


# Default Solhint configuration
DEFAULT_SOLHINT_CONFIG = {
    "extends": "solhint:recommended",
    "rules": {
        "compiler-version": ["error", "^0.8.0"],
        "func-visibility": ["warn", {"ignoreConstructors": True}],
        "max-line-length": ["warn", 120]
    }
}


def _find_project_root(start_path: str) -> Path:
    """
    Find the project root by walking up from start_path.
    Looks for indicators like .git, package.json, or .solhint.json.
    
    Args:
        start_path: Path to start searching from
        
    Returns:
        Path to project root, or current directory if not found
    """
    path = Path(start_path).resolve()
    
    # If it's a file, start from its parent directory
    if path.is_file():
        path = path.parent
    
    # Walk up the directory tree looking for project indicators
    for parent in [path] + list(path.parents):
        # Check for common project root indicators
        if any((parent / indicator).exists() for indicator in ['.git', 'package.json', 'foundry.toml', 'hardhat.config.js', 'hardhat.config.ts']):
            return parent
    
    # If no indicators found, return the directory containing the file
    return path


def _find_or_create_solhint_config(start_path: str) -> str:
    """
    Find or create a .solhint.json config file.
    
    Args:
        start_path: Path to start searching from
        
    Returns:
        Path to .solhint.json config file
    """
    path = Path(start_path).resolve()
    
    # If it's a file, start from its parent directory
    if path.is_file():
        path = path.parent
    
    # First, try to find existing config
    for parent in [path] + list(path.parents):
        config_file = parent / '.solhint.json'
        if config_file.exists():
            return str(config_file)
    
    # No config found - determine where to create it (project root)
    project_root = _find_project_root(start_path)
    config_file = project_root / '.solhint.json'
    
    # Create the default config file
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_SOLHINT_CONFIG, f, indent=2)
        return str(config_file)
    except (OSError, IOError):
        # If we can't write to project root, fall back to file's directory
        config_file = path / '.solhint.json'
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_SOLHINT_CONFIG, f, indent=2)
            return str(config_file)
        except (OSError, IOError):
            # If we still can't write, return None and let solhint use defaults
            return None


def run_solhint(file_path: str) -> Dict[str, Any]:
    """
    Run Solhint for best practices and return findings.
    
    Args:
        file_path: Path to the Solidity file to analyze
        
    Returns:
        Dictionary containing best practices findings
    """
    try:
        # Get absolute path to file
        abs_file_path = os.path.abspath(file_path)
        file_dir = os.path.dirname(abs_file_path)
        file_name = os.path.basename(abs_file_path)
        
        # Find or create a solhint config file
        config_path = _find_or_create_solhint_config(abs_file_path)
        
        # Build solhint command
        if config_path and os.path.exists(config_path):
            # Use explicit config file
            cmd = ["solhint", abs_file_path, "--formatter", "json", "--config", config_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Run from file's directory so solhint can find config relative to it
            cmd = ["solhint", file_name, "--formatter", "json"]
            result = subprocess.run(
                cmd,
                cwd=file_dir,
                capture_output=True,
                text=True,
                check=True
            )
        findings = json.loads(result.stdout)
        
        # Solhint outputs a list, not an object with "issues"
        if isinstance(findings, list):
            issues = findings
        else:
            issues = findings.get("issues", [])

        results = []
        for issue in issues:
            results.append({
                "issue": issue.get("message", "Unknown issue"),
                "severity": issue.get("severity", "info").capitalize(),
                "location": (
                    f"{issue.get('file', file_path)}:"
                    f"{issue.get('line', '?')}:"
                    f"{issue.get('column', '?')}"
                ),
                "category": "best_practice"
            })

        return {"best_practices": results}
    
    except subprocess.CalledProcessError as e:
        # Check if it's a config file error - if so, try running from file directory without explicit config
        stderr = e.stderr or ""
        if "config" in stderr.lower() and ("failed to load" in stderr.lower() or "cannot read" in stderr.lower()):
            try:
                # Retry by running from file's directory (different from first attempt if we used explicit config)
                abs_file_path = os.path.abspath(file_path)
                file_dir = os.path.dirname(abs_file_path)
                file_name = os.path.basename(abs_file_path)
                result = subprocess.run(
                    ["solhint", file_name, "--formatter", "json"],
                    cwd=file_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                findings = json.loads(result.stdout)
                
                if isinstance(findings, list):
                    issues = findings
                else:
                    issues = findings.get("issues", [])
                
                results = []
                for issue in issues:
                    results.append({
                        "issue": issue.get("message", "Unknown issue"),
                        "severity": issue.get("severity", "info").capitalize(),
                        "location": (
                            f"{issue.get('file', file_path)}:"
                            f"{issue.get('line', '?')}:"
                            f"{issue.get('column', '?')}"
                        ),
                        "category": "best_practice"
                    })
                
                return {"best_practices": results}
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                # If fallback also fails, return the original error
                pass
        
        error_msg = f"Solhint failed: {str(e)}"
        if stderr:
            error_msg += f"\nSTDERR: {stderr}"
        return {"error": error_msg}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Solhint JSON output: {str(e)}"}
    except FileNotFoundError:
        return {"error": "Solhint not found. Please install it: npm install -g solhint"}

