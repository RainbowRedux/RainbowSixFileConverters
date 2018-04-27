# Converts RSB files to png files and an acompanying JSON file with extra meta data
# information for file format from here:
# https://github.com/AlexKimov/RSE-file-formats/wiki/RSB-File-Format
# https://github.com/AlexKimov/RSE-file-formats/blob/master/010Editor-templates/RSB.bt
# RSB Version 0 required looking into the bt file directly as the wiki is not complete
# Texture and surface data extraction to JSON file is not complete

# On an i7-7700 conversion of the entire GOG copy of rainbow six takes around 4 minutes.
# This process could be heavily optimised if array slicing is minimised and more care is
# taken around memory copies, but since it's a once off process, I'm not too concerned with speed

#Files with DXT compressed images don't recover the image, since i haven't worked on decompressing DXT images
#Files with a format version later than 1 also store information after the image, currently this is discarded but can easily be added.

from PIL import Image
import time
import os
from os.path import isfile, join
import json

import BinaryConversionUtilities
from BinaryConversionUtilities import read_bitmask_ARGB_color
from RSBImageReader import RSBImageFile

def isByteArrayLargeEnoughForPalette(bytearray):
    paletteSize = 4 * 256
    if len(bytearray) < paletteSize:
        return False
    return True

def convert_RSB(filename):
    print("Processing: " + filename)

    imageFile = RSBImageFile()
    imageFile.read_RSB(filename)

    #create and save png from 256 color image
    if imageFile.image256 is not None:
        newImg1 = imageFile.convert_palette_image()
        newFilename = filename.replace(".RSB", "-256.PNG")
        newFilename = newFilename.replace(".rsb", "-256.PNG")
        newImg1.save(newFilename, "PNG")

    #create and save png from full color image
    newImg2 = imageFile.convert_full_color_image()
    newFilename = filename.replace(".RSB", ".PNG")
    newFilename = newFilename.replace(".rsb", ".PNG")
    newImg2.save(newFilename, "PNG")

    #save meta data to JSON file
    newFilename = newFilename.replace(".PNG", ".JSON")
    meta = BinaryConversionUtilities.MetaInfo()
    meta.setFilename(os.path.basename(filename))
    meta.add_info("header", imageFile.header)
    meta.writeJSON(newFilename)

    print("Finished converting: " + filename)
    print("")

def processAllFilesInFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            #print(os.path.join(root, name))
            if name.upper().endswith(".RSB"):
                convert_RSB(join(root, name))
        for name in dirs:
            print("Walking directory: " + os.path.join(root, name))

    print("Finished processing all data in folder")
    print("")
    return

def profile():
    import cProfile
    cProfile.run('processAllFilesInFolder("Data/R6")')

def main():
    """Main function that converts test data files"""
    #processAllFilesInFolder("Data/Test/Textures/RS/alphatesting")
    #return
    processAllFilesInFolder("Data/Test")
    return
    processAllFilesInFolder("Data/R6")
    processAllFilesInFolder("Data/RSDemo")

if __name__ == "__main__":
    main()
    #profile()
