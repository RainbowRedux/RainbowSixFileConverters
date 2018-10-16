from PIL import Image
import time
import os
from os.path import isfile, join
import json

from RainbowFileReaders import MAPLevelReader
from FileWriters import JSONMetaInfo, OBJModelWriter
from RainbowFileReaders.MathHelpers import is_vector_normal

def convert_MAP(filename):
    print("Processing: " + filename)

    modelFile = MAPLevelReader.MAPLevelFile()
    modelFile.read_map(filename, True)

    meta = JSONMetaInfo.JSONMetaInfo()
    meta.add_info("filecontents", modelFile)
    meta.add_info("filename", filename)
    newFilename = filename + ".JSON"
    meta.writeJSON(newFilename)

    print("===============================================")

def process_all_files_in_folder(folder):
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            #print(os.path.join(root, name))
            if name.upper().endswith(".MAP"):
                convert_MAP(join(root, name))
        for name in dirs:
            print("Walking directory: " + os.path.join(root, name))

    print("Finished processing all data in folder")
    print("")
    return

def profile():
    import cProfile
    cProfile.run('processAllFilesInFolder("Data/Test/R6")')

def main():
    """Main function that converts a test file"""
    paths = []
    #paths.append("../Data/Test/Maps/RS")
    paths.append("../Data/Test/")
    for path in paths:
        path = os.path.normpath(path)
        process_all_files_in_folder(path)

if __name__ == "__main__":
    main()
