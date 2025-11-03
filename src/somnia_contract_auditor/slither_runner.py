"""Slither analysis runner module."""

import json
import subprocess
from typing import Dict, List, Any


def _parse_slither_error(stderr: str, stdout: str, returncode: int) -> str:
    """
    Parse Slither error output to provide a more informative error message.
    
    Args:
        stderr: Standard error output from Slither
        stdout: Standard output from Slither
        returncode: Exit code from Slither
        
    Returns:
        Formatted error message
    """
    error_msg = f"Slither exited with code {returncode}"
    
    # Try to extract meaningful error from stderr or stdout
    error_text = stderr or stdout or ""
    
    # Common error patterns
    if "Compilation error" in error_text or "ParserError" in error_text:
        # Extract compilation errors
        lines = error_text.split('\n')
        error_lines = [line for line in lines if 'Error' in line or 'error' in line.lower()]
        if error_lines:
            error_msg += f"\nCompilation Error: {error_lines[0]}"
            # Include first few error lines
            if len(error_lines) > 1:
                error_msg += "\n" + "\n".join(error_lines[1:3])
    elif "No contracts were found" in error_text:
        error_msg += "\nNo contracts found in the file"
    elif "FileNotFoundError" in error_text or "No such file" in error_text:
        error_msg += "\nFile not found or cannot be read"
    elif "Import error" in error_text or "ImportError" in error_text:
        error_msg += "\nImport/dependency error - missing library or incorrect path"
    elif "Solc" in error_text or "solc" in error_text.lower():
        error_msg += "\nSolidity compiler issue - check compiler version"
    elif stderr:
        # Use first few lines of stderr if available
        stderr_lines = stderr.strip().split('\n')[:3]
        error_msg += f"\n{stderr_lines[0]}"
        if len(stderr_lines) > 1:
            error_msg += "\n" + "\n".join(stderr_lines[1:])
    elif stdout:
        # Sometimes errors go to stdout
        stdout_lines = stdout.strip().split('\n')[:3]
        error_msg += f"\n{stdout_lines[0]}"
    
    return error_msg


def run_slither(file_path: str) -> Dict[str, Any]:
    """
    Run Slither using CLI output and return parsed findings.
    
    Args:
        file_path: Path to the Solidity file to analyze
        
    Returns:
        Dictionary containing vulnerabilities, inefficiencies, and best practices
    """
    try:
        # Try running Slither with JSON output
        result = subprocess.run(
            ["slither", file_path, "--json", "-"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Slither exit codes:
        # 0: Success, no issues found
        # 255: Success, issues found (this is the default for --json)
        # 1: Error occurred
        # Other: Various errors
        
        data = None
        
        if result.returncode == 0:
            # Success, but might have empty output - try to parse anyway
            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Empty output means no issues
                    return {
                        "vulnerabilities": [],
                        "inefficiencies": [],
                        "best_practices": []
                    }
            else:
                # Empty output means no issues
                return {
                    "vulnerabilities": [],
                    "inefficiencies": [],
                    "best_practices": []
                }
        elif result.returncode == 255:
            # Issues found - parse the JSON output
            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {
                        "error": _parse_slither_error(result.stderr, result.stdout, result.returncode)
                    }
            else:
                return {
                    "vulnerabilities": [],
                    "inefficiencies": [],
                    "best_practices": []
                }
        else:
            # Error occurred (return code 1 or other)
            error_msg = _parse_slither_error(result.stderr, result.stdout, result.returncode)
            
            # Try alternative: run without JSON flag to see if we can get any output
            try:
                alt_result = subprocess.run(
                    ["slither", file_path],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                # If alternative run succeeds, we at least know the file is processable
                if alt_result.returncode in (0, 255):
                    # Return empty results but note there was an issue with JSON parsing
                    return {
                        "vulnerabilities": [],
                        "inefficiencies": [],
                        "best_practices": [],
                        "warning": "Slither analysis completed but JSON parsing failed. Check output manually."
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return {"error": error_msg}

        # Parse the JSON data (should be set by this point)
        if not data:
            return {
                "vulnerabilities": [],
                "inefficiencies": [],
                "best_practices": []
            }

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
    except subprocess.TimeoutExpired:
        return {"error": "Slither analysis timed out (>5 minutes). File may be too complex or have dependency issues."}
    except FileNotFoundError:
        return {"error": "Slither not found. Please install it: pip install slither-analyzer"}
    except Exception as e:
        return {"error": f"Unexpected error running Slither: {str(e)}"}


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

