"""Report generation module."""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Any


def generate_report(
    all_results: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]],
    sol_files: List[str],
    output_file: str = None
) -> Dict[str, Any]:
    """
    Generate Markdown report and return summary.
    
    Args:
        all_results: Dictionary mapping file paths to (slither_results, solhint_results)
        sol_files: List of scanned Solidity files
        output_file: Optional custom output file path
        
    Returns:
        Dictionary containing summary statistics and report file path
    """
    if output_file is None:
        output_file = f"audit-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(output_file, "w") as f:
        f.write(f"# Audit Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Files Scanned**: {len(sol_files)} ({', '.join(sol_files)})\n\n")
        f.write(f"**Mode**: Offline (Slither, Solhint)\n\n")

        # Per-file results
        for file_path, (slither_results, solhint_results) in all_results.items():
            f.write(f"## {os.path.basename(file_path)}\n")
            
            # Slither results
            if "error" in slither_results:
                f.write(f"### Slither Error\n")
                f.write(f"{slither_results['error']}\n\n")
            else:
                for category in ["vulnerabilities", "inefficiencies", "best_practices"]:
                    issues = slither_results.get(category, [])
                    if issues:
                        f.write(f"### {category.capitalize()}\n")
                        for issue in issues:
                            f.write(
                                f"- **{issue['severity']}**: "
                                f"{issue['issue']} at {issue['location']}\n"
                            )
                        f.write("\n")
            
            # Solhint results
            if "error" in solhint_results:
                f.write(f"### Solhint Error\n")
                f.write(f"{solhint_results['error']}\n\n")
            else:
                issues = solhint_results.get("best_practices", [])
                if issues:
                    f.write(f"### Best Practices (Solhint)\n")
                    for issue in issues:
                        f.write(
                            f"- **{issue['severity']}**: "
                            f"{issue['issue']} at {issue['location']}\n"
                        )
                    f.write("\n")
            
            f.write("\n")

        # Summary
        total_vulns = sum(
            len(r[0].get("vulnerabilities", [])) for r in all_results.values()
        )
        total_ineff = sum(
            len(r[0].get("inefficiencies", [])) for r in all_results.values()
        )
        total_bp = sum(
            len(r[0].get("best_practices", [])) + len(r[1].get("best_practices", []))
            for r in all_results.values()
        )
        total_issues = total_vulns + total_ineff + total_bp
        
        f.write("## Summary\n")
        f.write(f"- Total Issues: {total_issues}\n")
        f.write(f"- Vulnerabilities: {total_vulns}\n")
        f.write(f"- Inefficiencies: {total_ineff}\n")
        f.write(f"- Best Practices: {total_bp}\n")

    return {
        "total_issues": total_issues,
        "vulnerabilities": total_vulns,
        "inefficiencies": total_ineff,
        "best_practices": total_bp,
        "report_file": output_file
    }

