import os
import json
import subprocess
import glob
from datetime import datetime
from slither import Slither
from slither.exceptions import SlitherError
import click

# Output report file
REPORT_FILE = f"audit-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

def find_sol_files(path, recursive=True):
    """Find all .sol files in path (file, dir, or project)."""
    sol_files = []
    if os.path.isfile(path) and path.endswith('.sol'):
        sol_files = [path]
    elif os.path.isdir(path):
        if recursive:
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith('.sol'):
                        sol_files.append(os.path.join(root, file))
        else:
            sol_files = glob.glob(os.path.join(path, '*.sol'))
    else:
        # Assume current dir project scan
        project_dirs = ['src', 'contracts']
        for dir_name in project_dirs:
            if os.path.exists(dir_name):
                for root, _, files in os.walk(dir_name):
                    for file in files:
                        if file.endswith('.sol'):
                            sol_files.append(os.path.join(root, file))
        if not sol_files:
            # Fallback: all .sol in current dir
            sol_files = glob.glob('*.sol')
    return sol_files if sol_files else []

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
        error_msg = f"Solhint failed: {str(e)}"
        if isinstance(e, subprocess.CalledProcessError):
            error_msg += f"\nSTDERR: {e.stderr}"
        return {"error": error_msg}

def generate_report(all_results, sol_files):
    """Generate Markdown report and return summary."""
    with open(REPORT_FILE, "w") as f:
        f.write(f"# Audit Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Files Scanned**: {len(sol_files)} ({', '.join(sol_files)})\n\n")
        f.write(f"**Mode**: Offline (Slither, Solhint)\n\n")

        # Per-file results
        for file_path, (slither_results, solhint_results) in all_results.items():
            f.write(f"## {os.path.basename(file_path)}\n")
            if "error" in slither_results:
                f.write(f"Slither Error: {slither_results['error']}\n")
            else:
                for category in ["vulnerabilities", "inefficiencies", "best_practices"]:
                    f.write(f"### {category.capitalize()}\n")
                    for issue in slither_results.get(category, []):
                        f.write(f"- **{issue['severity']}**: {issue['issue']} at {issue['location']}\n")
            if "error" in solhint_results:
                f.write(f"Solhint Error: {solhint_results['error']}\n")
            else:
                for issue in solhint_results.get("best_practices", []):
                    f.write(f"- **{issue['severity']}**: {issue['issue']} at {issue['location']}\n")
            f.write("\n")

        # Summary
        total_vulns = sum(len(r[0].get("vulnerabilities", [])) for r in all_results.values())
        total_ineff = sum(len(r[0].get("inefficiencies", [])) for r in all_results.values())
        total_bp = sum(len(r[0].get("best_practices", [])) + len(r[1].get("best_practices", [])) for r in all_results.values())
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
        "report_file": REPORT_FILE
    }

@click.command()
@click.argument('path', default='.', nargs=1)
@click.option('--recursive', is_flag=True, default=True, help='Recursive dir scan')
def audit(path, recursive):
    """Run offline audit on path (file/dir/project)."""
    sol_files = find_sol_files(path, recursive)
    if not sol_files:
        click.echo("No .sol files found.")
        return

    click.echo(f"Scanning {len(sol_files)} files...")
    all_results = {}
    for file_path in sol_files:
        click.echo(f"  - {file_path}")
        slither_results = run_slither(file_path)
        solhint_results = run_solhint(file_path)
        all_results[file_path] = (slither_results, solhint_results)
        if "error" in slither_results or "error" in solhint_results:
            click.echo(f"    Errors in {os.path.basename(file_path)}")

    summary = generate_report(all_results, sol_files)
    click.echo("\nAudit Summary:")
    click.echo(f"- Total Issues: {summary['total_issues']}")
    click.echo(f"- Vulnerabilities: {summary['vulnerabilities']}")
    click.echo(f"- Inefficiencies: {summary['inefficiencies']}")
    click.echo(f"- Best Practices: {summary['best_practices']}")
    click.echo(f"- Report saved to: {summary['report_file']}")

if __name__ == "__main__":
    audit()