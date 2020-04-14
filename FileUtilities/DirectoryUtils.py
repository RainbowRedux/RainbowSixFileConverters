"""
Commonly used functions for directories
"""
import os
from os import path

from typing import List

def gather_files_in_path(extension: str, folder: str) -> List[str]:
    """Walks a folder and it's sub directories and finds all files with matching extension, case-insensitive"""
    filesToProcess = []
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            if name.upper().endswith(extension.upper()):
                filesToProcess.append(path.join(root, name))
        for name in dirs:
            pass
    return filesToProcess
