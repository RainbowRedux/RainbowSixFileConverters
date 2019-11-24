"""
Commonly used functions for directories
"""
import os
from os.path import join

def gather_files_in_path(extension, folder):
    """Walks a folder and it's sub directories and finds all files with matching extension, case-insensitive"""
    filesToProcess = []
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            if name.upper().endswith(extension.upper()):
                filesToProcess.append(join(root, name))
        for name in dirs:
            pass
            #print("Walking directory: " + os.path.join(root, name))
    return filesToProcess
