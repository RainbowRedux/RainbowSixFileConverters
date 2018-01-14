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
from BinaryConversionUtilities import bytes_to_int, bytes_to_uint, bytes_to_float, bytes_to_shortint, read_bgra_color, read_bitmask_RGBA_color

class SOBHeader(object):
    def __init__(self):
        self.headerLength = 0
        self.headerBeginMessage = None

    def read_header(self, bytearray):
        num_bytes_processed = 0
        
        self.headerLength = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.headerBeginMessage = bytearray[num_bytes_processed:num_bytes_processed+self.headerLength-1]
        num_bytes_processed += self.headerLength

        return num_bytes_processed

    def print_header_info(self):
        print "Header length: " + str(self.headerLength)
        print "Header message: " + self.headerBeginMessage
        print ""

class MaterialListHeader(object):
    def __init__(self):
        pass

    def read_header(self, bytearray):
        num_bytes_processed = 0

        self.materialListSize = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.unknown1 = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.materialBeginMessageLength = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.materialBeginMessage = bytearray[num_bytes_processed:num_bytes_processed + self.materialBeginMessageLength - 1]
        num_bytes_processed += self.materialBeginMessageLength

        self.numMaterials = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        return num_bytes_processed

    def print_header_info(self):
        print "Material list size: " + str(self.materialListSize)
        print "unknown1: " + str(self.unknown1)
        print "Number of materials: " + str(self.numMaterials)
        print "Begin message length: " + str(self.materialBeginMessageLength)
        print "Begin message: " + self.materialBeginMessage
        print ""


class MaterialDefinition(object):
    def __init__(self):
        pass

    def read_material(self, bytearray):
        num_bytes_processed = 0

        self.materialSize = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.unknown1 = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.materialNameLength = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.materialName = bytearray[num_bytes_processed:num_bytes_processed + self.materialNameLength - 1]
        num_bytes_processed += self.materialNameLength

        self.textureNameLength = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.textureName = bytearray[num_bytes_processed:num_bytes_processed + self.textureNameLength - 1]
        num_bytes_processed += self.textureNameLength

        self.opacity = bytes_to_float(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.unknown2 = bytes_to_float(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.ambient = BinaryConversionUtilities.read_uint_array(bytearray[num_bytes_processed:], 4)
        #4 uints of 4 bytes each
        num_bytes_processed += 4*4

        self.diffuse = BinaryConversionUtilities.read_uint_array(bytearray[num_bytes_processed:], 3)
        #3 uints of 4 bytes each
        num_bytes_processed += 3*4

        self.specular = BinaryConversionUtilities.read_uint_array(bytearray[num_bytes_processed:], 3)
        #3 uints of 4 bytes each
        num_bytes_processed += 3*4

        self.specularLevel = bytes_to_float(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.twoSided = bytearray[num_bytes_processed]
        num_bytes_processed += 1

        return num_bytes_processed

    def print_material_info(self):
        print "Material size: " + str(self.materialSize)
        print "unknown1: " + str(self.unknown1)
        print "Material Name Length: " + str(self.materialNameLength)
        print "Material Name " + self.materialName
        print "Texture Name Length: " + str(self.textureNameLength)
        print "Texture Name: " + self.textureName
        print ""

def convert_SOB(filename):
    print "Processing: " + filename
    f = open(filename, "rb")

    bytes_read = f.read()

    f.close()

    num_bytes_processed = 0
    
    #read header
    header = SOBHeader()
    num_bytes_processed += header.read_header(bytes_read)
    header.print_header_info()

    matHeader = MaterialListHeader()
    num_bytes_processed += matHeader.read_header(bytes_read[num_bytes_processed:])
    matHeader.print_header_info()

    print num_bytes_processed
    if matHeader.numMaterials > 1:
        num_bytes_processed += 20

    print num_bytes_processed

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


    print "Processed " + str(num_bytes_processed) + " bytes"
    print "Length " + str(len(bytes_read)) + " bytes"
    print str(len(bytes_read) - num_bytes_processed) + " unprocessed bytes"
    print "Finished!"
    print ""

def processAllFilesInFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            #print(os.path.join(root, name))
            if name.upper().endswith(".SOB"):
                convert_SOB(join(root, name))
        for name in dirs:
            print("Walking directory: " + os.path.join(root, name))

    print "Finished processing all data in folder"
    print ""
    return

def main():
    """Main function that converts a test file"""
    processAllFilesInFolder("Data/Test")
    return
if __name__ == "__main__":
    main()
