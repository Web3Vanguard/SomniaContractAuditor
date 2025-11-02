"""Solhint analysis runner module."""

import json
import subprocess
from typing import Dict, List, Any


def run_solhint(file_path: str) -> Dict[str, Any]:
    """
    Run Solhint for best practices and return findings.
    
    Args:
        file_path: Path to the Solidity file to analyze
        
    Returns:
        Dictionary containing best practices findings
    """
    try:
        result = subprocess.run(
            ["solhint", file_path, "--formatter", "json"],
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
        error_msg = f"Solhint failed: {str(e)}"
        if e.stderr:
            error_msg += f"\nSTDERR: {e.stderr}"
        return {"error": error_msg}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Solhint JSON output: {str(e)}"}
    except FileNotFoundError:
        return {"error": "Solhint not found. Please install it: npm install -g solhint"}

