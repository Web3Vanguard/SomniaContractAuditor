"""File discovery module for finding Solidity files."""

import os
import glob
from typing import List


def find_sol_files(path: str, recursive: bool = True) -> List[str]:
    """
    Find all .sol files in path (file, dir, or project).
    
    Args:
        path: File path, directory path, or project root
        recursive: Whether to search recursively in directories
        
    Returns:
        List of .sol file paths
    """
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

