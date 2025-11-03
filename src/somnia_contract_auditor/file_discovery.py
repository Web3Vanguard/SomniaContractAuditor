"""File discovery module for finding Solidity files."""

import os
import glob
from typing import List, Set


# Default folders to exclude (library and build artifacts)
DEFAULT_EXCLUDE_DIRS = {
    'lib',           # Foundry dependencies
    'node_modules',  # Hardhat/NPM dependencies
    '.git',          # Version control
    'cache',         # Build cache (Foundry)
    'out',           # Build output (Hardhat)
    'artifacts',    # Build artifacts (Hardhat)
    '.cache',        # Cache directories
}


def _should_exclude_path(root: str, exclude_dirs: Set[str]) -> bool:
    """
    Check if a directory path should be excluded.
    
    Args:
        root: Directory path to check
        exclude_dirs: Set of directory names to exclude
        
    Returns:
        True if path should be excluded, False otherwise
    """
    # Split path into components
    path_parts = os.path.normpath(root).split(os.sep)
    
    # Check if any component matches an excluded directory
    for part in path_parts:
        if part in exclude_dirs:
            return True
    
    return False


def find_sol_files(
    path: str,
    recursive: bool = True,
    include_libs: bool = False
) -> List[str]:
    """
    Find all .sol files in path (file, dir, or project).
    
    Args:
        path: File path, directory path, or project root
        recursive: Whether to search recursively in directories
        include_libs: If True, include library folders (lib/, node_modules/)
                     If False, exclude them by default
        
    Returns:
        List of .sol file paths
    """
    sol_files = []
    
    # Determine which directories to exclude
    exclude_dirs = set() if include_libs else DEFAULT_EXCLUDE_DIRS
    
    if os.path.isfile(path) and path.endswith('.sol'):
        sol_files = [path]
    elif os.path.isdir(path):
        if recursive:
            for root, dirs, files in os.walk(path):
                # Prune excluded directories from os.walk
                if not include_libs:
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                # Skip this directory if it should be excluded
                if _should_exclude_path(root, exclude_dirs):
                    continue
                
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
                for root, dirs, files in os.walk(dir_name):
                    # Prune excluded directories from os.walk
                    if not include_libs:
                        dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    
                    # Skip this directory if it should be excluded
                    if _should_exclude_path(root, exclude_dirs):
                        continue
                    
                    for file in files:
                        if file.endswith('.sol'):
                            sol_files.append(os.path.join(root, file))
        if not sol_files:
            # Fallback: all .sol in current dir
            sol_files = glob.glob('*.sol')
    
    return sol_files if sol_files else []

