# Quick Start Guide

## Installation

### Option 1: Install from Source

```bash
pip install -e .
```

This installs the `somnia-auditor` command globally.

### Option 2: Use the Binary

The project includes a pre-built binary (if available) or you can build your own:

```bash
python build_binary.py
```

Then use it directly:
```bash
./dist/somnia-auditor audit contract.sol
```

## Prerequisites

Before using the auditor, ensure you have the required tools installed:

1. **Slither**: `pip install slither-analyzer`
2. **Solhint**: `npm install -g solhint`

## Basic Usage

```bash
# Audit a single file
somnia-auditor audit contract.sol

# Audit current directory (recursive)
somnia-auditor audit

# Audit specific directory
somnia-auditor audit ./contracts

# Custom output file
somnia-auditor audit -o my-report.md

# Quiet mode
somnia-auditor audit -q
```

## Viewing Results

After running an audit, check the generated markdown report for:
- Vulnerabilities (security issues)
- Inefficiencies (gas optimizations)
- Best Practices (code quality)

The report file is named `audit-report-YYYYMMDD_HHMMSS.md` by default.
