<p align="center">
  <img src="assets/logo.svg" alt="Somnia Contract Auditor" width="520" />
</p>

# Somnia Contract Auditor

A smart contract auditing tool that performs static analysis on Solidity contracts using Slither and Solhint.

## Features

- 🔍 **Static Analysis**: Analyzes Solidity contracts for vulnerabilities, inefficiencies, and best practices
- 🛠️ **Multiple Tools**: Integrates Slither and Solhint for comprehensive auditing
- 📊 **Detailed Reports**: Generates markdown reports with categorized findings
- 🚀 **CLI Interface**: Easy-to-use command-line interface
- 📦 **Standalone Binary**: Can be built as a standalone executable
- 🎯 **Smart Exclusions**: Automatically excludes library folders (lib/, node_modules/) by default

## Installation

### From Installer

```bash
curl -fsSL https://raw.githubusercontent.com/Web3Vanguard/SomniaContractAuditor/refs/heads/main/scripts/install.sh | bash
```

# or

```bash
curl -fsSL https://raw.githubusercontent.com/Web3Vanguard/SomniaContractAuditor/refs/heads/main/scripts/install.sh | sudo bash
```

### From Source

```bash
# Clone the repository
git clone https://github.com/Web3Vanguard/SomniaContractAuditor.git
cd SomniaContractAuditor

# Install in development mode
pip install -e .

# Or install in production mode
pip install .
```

### Prerequisites

The tool requires external dependencies:

1. **Slither**: `pip install slither-analyzer`
2. **Solhint**: `npm install -g solhint`

## Usage

### Basic Usage

```bash
# Audit current directory (recursive)
somnia-auditor audit

# Audit a specific file
somnia-auditor audit contract.sol

# Audit a directory
somnia-auditor audit ./contracts

# Audit without recursion
somnia-auditor audit ./src --no-recursive

# Specify output file
somnia-auditor audit -o my-report.md

# Quiet mode (suppress progress)
somnia-auditor audit -q

# Include library folders (lib/, node_modules/)
somnia-auditor audit --include-libs
```

### As a Python Module

```bash
python -m somnia_contract_auditor audit contract.sol
```

### Help

```bash
somnia-auditor --help
somnia-auditor audit --help
```

## Building a Standalone Binary

To create a standalone executable binary:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the binary
python build_binary.py

# Or use the Makefile
make binary
```

The binary will be created in the `dist/` directory:
- Linux/macOS: `dist/somnia-auditor`
- Windows: `dist/somnia-auditor.exe`

The binary is a standalone executable that includes all dependencies. You can distribute it without requiring users to install Python or any dependencies.

### Using the Binary

After building, you can use the binary directly:

```bash
./dist/somnia-auditor audit contract.sol
```

## Project Structure

```
SomniaContractAuditor/
├── src/
│   └── somnia_contract_auditor/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py              # CLI entry point
│       ├── file_discovery.py   # File finding logic
│       ├── slither_runner.py   # Slither integration
│       ├── solhint_runner.py   # Solhint integration
│       └── report_generator.py # Report generation
├── pyproject.toml              # Project configuration
├── requirements.txt            # Python dependencies
├── build_binary.py             # Binary build script
├── entry_point.py              # Standalone entry point for binary
├── somnia-auditor.spec         # PyInstaller spec file
└── README.md                   # This file
```

## Default Exclusions

By default, the following folders are excluded from scanning:
- `lib/` - Foundry dependencies
- `node_modules/` - Hardhat/NPM dependencies  
- `.git/` - Version control
- `cache/`, `out/`, `artifacts/` - Build artifacts

Use the `--include-libs` flag if you want to audit library code as well.

## Report Format

The generated audit reports include:

- **Vulnerabilities**: Security issues that could be exploited
- **Inefficiencies**: Gas optimization opportunities
- **Best Practices**: Code quality and style recommendations

## Development

### Setting up Development Environment

```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
```
