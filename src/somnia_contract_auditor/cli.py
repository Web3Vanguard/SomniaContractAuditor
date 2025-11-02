"""Command-line interface for Somnia Contract Auditor."""

import os
import sys
import click
from typing import Dict, Tuple, Any

from .file_discovery import find_sol_files
from .slither_runner import run_slither
from .solhint_runner import run_solhint
from .report_generator import generate_report


@click.group()
@click.version_option(version="1.0.0", prog_name="somnia-auditor")
def cli():
    """Somnia Contract Auditor - A production-ready smart contract auditing tool."""
    pass


@cli.command()
@click.argument('path', default='.', type=click.Path(exists=True))
@click.option(
    '--recursive/--no-recursive',
    default=True,
    help='Recursive directory scan (default: True)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Custom output file path for the report'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress progress output'
)
def audit(path: str, recursive: bool, output: str, quiet: bool):
    """
    Run offline audit on path (file/dir/project).
    
    PATH can be a file, directory, or project root.
    """
    sol_files = find_sol_files(path, recursive)
    
    if not sol_files:
        click.echo("No .sol files found.", err=True)
        sys.exit(1)

    if not quiet:
        click.echo(f"Scanning {len(sol_files)} files...")
    
    all_results: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    
    for file_path in sol_files:
        if not quiet:
            click.echo(f"  - {file_path}")
        
        slither_results = run_slither(file_path)
        solhint_results = run_solhint(file_path)
        
        all_results[file_path] = (slither_results, solhint_results)
        
        if "error" in slither_results or "error" in solhint_results:
            if not quiet:
                click.echo(f"    Errors in {os.path.basename(file_path)}")

    summary = generate_report(all_results, sol_files, output_file=output)

    if not quiet:
        click.echo("\nAudit Summary:")
        click.echo(f"- Total Issues: {summary['total_issues']}")
        click.echo(f"- Vulnerabilities: {summary['vulnerabilities']}")
        click.echo(f"- Inefficiencies: {summary['inefficiencies']}")
        click.echo(f"- Best Practices: {summary['best_practices']}")
        click.echo(f"- Report saved to: {summary['report_file']}")
    
    # Exit with non-zero code if vulnerabilities found
    if summary['vulnerabilities'] > 0:
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

