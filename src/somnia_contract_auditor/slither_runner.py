"""Slither analysis runner module."""

import json
import subprocess
from typing import Dict, List, Any


def run_slither(file_path: str) -> Dict[str, Any]:
    """
    Run Slither using CLI output and return parsed findings.
    
    Args:
        file_path: Path to the Solidity file to analyze
        
    Returns:
        Dictionary containing vulnerabilities, inefficiencies, and best practices
    """
    try:
        result = subprocess.run(
            ["slither", file_path, "--json", "-"],
            capture_output=True,
            text=True
        )

        # Accept exit code 0 (clean) or 255 (issues found)
        if result.returncode not in (0, 255):
            return {"error": f"Slither exited with code {result.returncode}: {result.stderr}"}

        data = json.loads(result.stdout)

        results = []
        for detector in data.get("results", {}).get("detectors", []):
            description = detector.get("description", "")
            impact = detector.get("impact", "Info")
            elements = detector.get("elements", [])
            for element in elements:
                source_mapping = element.get("source_mapping", {})
                location = (
                    f"{source_mapping.get('filename_short', file_path)}:"
                    f"{source_mapping.get('lines', '?')}"
                )
                results.append({
                    "issue": description,
                    "severity": impact,
                    "location": location,
                    "category": _categorize_issue(description)
                })

        return {
            "vulnerabilities": [r for r in results if r["category"] == "vulnerability"],
            "inefficiencies": [r for r in results if r["category"] == "inefficiency"],
            "best_practices": [r for r in results if r["category"] == "best_practice"]
        }

    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Slither JSON output: {str(e)}"}
    except FileNotFoundError:
        return {"error": "Slither not found. Please install it: pip install slither-analyzer"}


def _categorize_issue(description: str) -> str:
    """
    Categorize an issue based on its description.
    
    Args:
        description: Issue description
        
    Returns:
        Category string: "vulnerability", "inefficiency", or "best_practice"
    """
    desc_lower = description.lower()
    if "reentrancy" in desc_lower or "vulnerability" in desc_lower:
        return "vulnerability"
    elif "gas" in desc_lower or "optimization" in desc_lower:
        return "inefficiency"
    else:
        return "best_practice"

