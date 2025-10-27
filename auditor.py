import os
import json
import subprocess
from datetime import datetime
from slither import Slither
from slither.exceptions import SlitherError
import click

# Hardcoded path to Solidity file
CONTRACT_PATH = "./contract.sol"

# Output report file
REPORT_FILE = f"audit-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

def run_slither(file_path):
    """Run Slither using CLI output and return parsed findings."""
    try:
        result = subprocess.run(
            ["slither", file_path, "--json", "-"],
            capture_output=True, text=True
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
                location = f"{source_mapping.get('filename_short', file_path)}:{source_mapping.get('lines', '?')}"
                results.append({
                    "issue": description,
                    "severity": impact,
                    "location": location,
                    "category": "vulnerability" if "reentrancy" in description.lower()
                    else "inefficiency" if "gas" in description.lower() or "optimization" in description.lower()
                    else "best_practice"
                })

        return {
            "vulnerabilities": [r for r in results if r["category"] == "vulnerability"],
            "inefficiencies": [r for r in results if r["category"] == "inefficiency"],
            "best_practices": [r for r in results if r["category"] == "best_practice"]
        }

    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Slither JSON output: {str(e)}"}

def run_solhint(file_path):
    """Run Solhint for best practices and return findings."""
    try:
        result = subprocess.run(
            ["solhint", file_path, "--formatter", "json"],
            capture_output=True, text=True, check=True
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
                "location": f"{issue.get('file', file_path)}:{issue.get('line', '?')}:{issue.get('column', '?')}",
                "category": "best_practice"
            })

        return {"best_practices": results}

    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        return {"error": f"Solhint failed: {str(e)}"}

def generate_report(slither_results, solhint_results):
    """Generate Markdown report and return summary."""
    with open(REPORT_FILE, "w") as f:
        f.write(f"# Audit Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**File Scanned**: {CONTRACT_PATH}\n\n")
        f.write(f"**Mode**: Offline (Slither, Solhint)\n\n")

        # Slither Results
        if "error" in slither_results:
            f.write(f"## Slither Error\n- {slither_results['error']}\n")
        else:
            f.write("## Slither Findings\n")
            for category in ["vulnerabilities", "inefficiencies", "best_practices"]:
                f.write(f"### {category.capitalize()}\n")
                for issue in slither_results.get(category, []):
                    f.write(f"- **{issue['severity']}**: {issue['issue']} at {issue['location']}\n")

        # Solhint Results
        if "error" in solhint_results:
            f.write(f"## Solhint Error\n- {solhint_results['error']}\n")
        else:
            f.write("## Solhint Findings\n")
            for issue in solhint_results.get("best_practices", []):
                f.write(f"- **{issue['severity']}**: {issue['issue']} at {issue['location']}\n")

        # Summary
        total_issues = (
            len(slither_results.get("vulnerabilities", [])) +
            len(slither_results.get("inefficiencies", [])) +
            len(slither_results.get("best_practices", [])) +
            len(solhint_results.get("best_practices", []))
        )
        f.write("\n## Summary\n")
        f.write(f"- Total Issues: {total_issues}\n")
        f.write(f"- Vulnerabilities: {len(slither_results.get('vulnerabilities', []))}\n")
        f.write(f"- Inefficiencies: {len(slither_results.get('inefficiencies', []))}\n")
        f.write(f"- Best Practices: {len(slither_results.get('best_practices', [])) + len(solhint_results.get('best_practices', []))}\n")

    return {
        "total_issues": total_issues,
        "vulnerabilities": len(slither_results.get("vulnerabilities", [])),
        "inefficiencies": len(slither_results.get("inefficiencies", [])),
        "best_practices": len(slither_results.get("best_practices", [])) + len(solhint_results.get("best_practices", [])),
        "report_file": REPORT_FILE
    }

@click.command()
def audit():
    """Run offline audit on hardcoded Solidity file."""
    if not os.path.exists(CONTRACT_PATH):
        click.echo(f"Error: File not found at {CONTRACT_PATH}")
        return

    click.echo(f"Scanning {CONTRACT_PATH}...")
    slither_results = run_slither(CONTRACT_PATH)
    solhint_results = run_solhint(CONTRACT_PATH)

    if "error" in slither_results or "error" in solhint_results:
        click.echo("Errors occurred during scan:")
        if "error" in slither_results:
            click.echo(f"Slither: {slither_results['error']}")
        if "error" in solhint_results:
            click.echo(f"Solhint: {solhint_results['error']}")
        return

    summary = generate_report(slither_results, solhint_results)
    click.echo("\nAudit Summary:")
    click.echo(f"- Total Issues: {summary['total_issues']}")
    click.echo(f"- Vulnerabilities: {summary['vulnerabilities']}")
    click.echo(f"- Inefficiencies: {summary['inefficiencies']}")
    click.echo(f"- Best Practices: {summary['best_practices']}")
    click.echo(f"- Report saved to: {summary['report_file']}")

if __name__ == "__main__":
    audit()