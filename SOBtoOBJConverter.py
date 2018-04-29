#Converts RSB files to png files and an acompanying JSON file with extra meta data
#information for file format from here:
#https://github.com/AlexKimov/RSE-file-formats/wiki/RSB-File-Format
#https://github.com/AlexKimov/RSE-file-formats/blob/master/010Editor-templates/RSB.bt
#RSB Version 0 required looking into the bt file directly as the wiki is not complete
#Texture and surface data extraction to JSON file is not complete

from PIL import Image
import time
import os
from os.path import isfile, join
import json

import BinaryConversionUtilities

from SOBModelReader import SOBModelFile

def convert_SOB(filename):
    print("Processing: " + filename)

    modelFile = SOBModelFile()
    modelFile.read_sob(filename)

    num_bytes_processed = 0

    meta = BinaryConversionUtilities.MetaInfo()
    meta.add_info("filecontents", modelFile)
    meta.add_info("filename", filename)
    newFilename = filename + ".JSON"
    meta.writeJSON(newFilename)

    print("===============================================")

    return

    print(str(num_bytes_processed))
    if matHeader.numMaterials > 1:
        num_bytes_processed += 20

    print(str(num_bytes_processed))

    materials = []

    for i in xrange(matHeader.numMaterials):
        matDef = MaterialDefinition()
        num_bytes_processed += matDef.read_material(bytes_read[num_bytes_processed:])
        matDef.print_material_info()
        materials.append(matDef)

    #header.print_header_info()

    newFilename = filename.replace(".SOB", ".JSON")
    newFilename = newFilename.replace(".sob", ".JSON")
    meta = BinaryConversionUtilities.MetaInfo()
    meta.setFilename(os.path.basename(filename))
    meta.add_info("header", header)
    meta.add_info("materialSectionHeader", matHeader)
    meta.add_info("materials", materials)
    meta.writeJSON(newFilename)

    print("Finished!")
    print("")

def processAllFilesInFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            #print(os.path.join(root, name))
            if name.upper().endswith(".SOB"):
                convert_SOB(join(root, name))
        for name in dirs:
            print("Walking directory: " + os.path.join(root, name))

    print("Finished processing all data in folder")
    print("")
    return

def profile():
    import cProfile
    cProfile.run('processAllFilesInFolder("Data/Test")')

def main():
    """Main function that converts a test file"""
    processAllFilesInFolder("Data/Test")
    return
if __name__ == "__main__":
    main()
