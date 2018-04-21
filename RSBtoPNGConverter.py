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
from BinaryConversionUtilities import bytes_to_uint, bytes_to_int, bytes_to_shortint, read_bgra_color, read_bitmask_RGBA_color

class RSBHeader(object):
    """Class that matches the RSB file format header"""
    def __init__(self):
        self.version = None
        self.width = None
        self.height = None
        self.containsPalette = None
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None
        self.bitDepthRed = None
        self.bitDepthGreen = None
        self.bitDepthBlue = None
        self.bitDepthAlpha = None
        self.isDXT = False
        self.dxtType = None

    def isPowerOf2(self):
        """Checks if the dimensions of the image are power of 2, and therefore are likely to be gameplay textures with 256 colour versions stored"""
        num1 = self.width != 0 and ((self.width & (self.width - 1)) == 0)
        num2 = self.height != 0 and ((self.height & (self.height - 1)) == 0)
        return num1 and num2

    def isValid(self):
        """Some images cause errors when converting, they seem to have invalid headers. Simple checks here identify bad headers"""
        if self.bitDepthAlpha + self.bitDepthBlue + self.bitDepthGreen + self.bitDepthRed == 0:
            return False
        if self.bitDepthAlpha + self.bitDepthBlue + self.bitDepthGreen + self.bitDepthRed > 32:
            return False
        return True

    def calculate_bytes_per_pixel(self):
        """Calculates how many bytes per pixel are to be expected in the images"""
        if self.isDXT:
            if self.dxtType == 0:
                return 1
            else:
                return 2
        else:
            bitDepthTotal = self.bitDepthRed + self.bitDepthGreen + self.bitDepthBlue + self.bitDepthAlpha
            return bitDepthTotal / 8

    def print_header_info(self):
        print "RSB Version: " + str(self.version)
        print "Image Width: " + str(self.width)
        print "Image height: " + str(self.height)
        if self.bitDepthAlpha > 0:
            print "Has Alpha?: True"
        else:
            print "Has Alpha?: False"
        print "BitDepthRed: " + str(self.bitDepthRed)
        print "BitDepthGreen: " + str(self.bitDepthGreen)
        print "BitDepthBlue: " + str(self.bitDepthBlue)
        print "BitDepthAlpha: " + str(self.bitDepthAlpha)
        print "containsPalette: " + str(self.containsPalette)
        print "Unknown var2: " + str(self.unknown2)
        print "Unknown var3: " + str(self.unknown3)
        print "Unknown var4: " + str(self.unknown4)
        print "Unknown var5: " + str(self.unknown5)
        print "isDXT: " + str(self.isDXT)
        print "DXT Type: " + str(self.dxtType)

    def read_bit_mask(self, bytearray):
        """Reads the bitmask for each color channel. May be stored outside of the header in Version 0 files"""
        num_bytes_processed = 0
        #bit depth information
        self.bitDepthRed = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.bitDepthGreen = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.bitDepthBlue = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.bitDepthAlpha = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4
        
        return num_bytes_processed

    def read_header(self, bytearray):
        num_bytes_processed = 0
        self.version = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.width = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        self.height = bytes_to_uint(bytearray[num_bytes_processed:])
        num_bytes_processed += 4

        if self.version == 0:
            self.containsPalette = bytes_to_uint(bytearray[num_bytes_processed:])
            num_bytes_processed += 4

        #num_bytes_processed += 1
        if self.version > 7:
            #process 3 more variables
            self.unknown2 = bytes_to_uint(bytearray[num_bytes_processed:])
            num_bytes_processed += 4

            self.unknown3 = bytes_to_uint(bytearray[num_bytes_processed:])
            num_bytes_processed += 4

            self.unknown4 = bytearray[num_bytes_processed:num_bytes_processed+1]
            num_bytes_processed += 1

        if self.version > 0:
            #bit depth information
            print num_bytes_processed
            num_bytes_processed += self.read_bit_mask(bytearray[num_bytes_processed:])

        if self.version >= 9: 
            self.unknown5 = bytes_to_uint(bytearray[num_bytes_processed:])
            num_bytes_processed += 4

            self.dxtType = bytes_to_uint(bytearray[num_bytes_processed:])
            num_bytes_processed += 4
            if self.dxtType >= 0 and self.dxtType < 5:
                self.isDXT = True

        return num_bytes_processed

class RSBPalette(object):
    """Reads and stores the color palette of version 0 files"""
    def __init__(self):
        self.num_palette_entries = 256
        self.palette_entries = []
        pass
    
    def get_color(self, index):
        return self.palette_entries[index]

    def print_palette(self):
        for color in self.palette_entries:
            print "R: " + str(color[0]) + "\tG: " + str(color[1]) + "\tB: " + str(color[2]) + "\tA: " + str(color[3])

    def read_palette(self, bytearray):
        num_bytes_processed = 0
        self.palette_entries = []
        for i in xrange(self.num_palette_entries):
            temp = read_bgra_color(bytearray[num_bytes_processed:])
            num_bytes_processed += 4
            self.palette_entries.append(temp)
        return num_bytes_processed

class RSBImage(object):
    """Reads and stores the image data of RSB files"""
    def __init__(self):
        self.image = []
        pass
    
    def get_pixel(self, index):
        if index >= len(self.image):
            print "Invalid index: " + str(index)
            return "0"
        return self.image[index]

    def read_image(self, width, height, bytes_per_pixel, bytearray):
        num_bytes_processed = 0
        self.image = []
        for i in xrange(width*height):
            self.image.append(bytearray[num_bytes_processed : num_bytes_processed + bytes_per_pixel])
            num_bytes_processed += bytes_per_pixel
        return num_bytes_processed


def isByteArrayLargeEnoughForPalette(bytearray):
    paletteSize = 4 * 256
    if len(bytearray) < paletteSize:
        return False
    return True

def convert_RSB(filename):
    print "Processing: " + filename

    #read entire file
    f = open(filename, "rb")
    bytes_read = f.read()
    f.close()

    num_bytes_processed = 0
    
    #read header
    header = RSBHeader()
    num_bytes_processed += header.read_header(bytes_read)

    image256 = None

    #read information that only exists in file format version 0 under certain circumstances
    #the 256 color image is only stored for textures that are used in game, not UI elements
    #these simple condition checks are enough to accurately filter out all UI elements, the other option is filter based on folder
    if header.version == 0 and header.containsPalette == 1:
        #read palette
        palette = None
        palette = RSBPalette()
        num_bytes_processed += palette.read_palette(bytes_read[num_bytes_processed:])
        #palette.print_palette()

        #read 256 color image
        image256 = RSBImage()
        bytesPerPixel = 1
        num_bytes_processed += image256.read_image(header.width, header.height, bytesPerPixel, bytes_read[num_bytes_processed:])

    #in version 0 files, the bit mask is stored after the palette version of the image
    if header.version == 0:
        num_bytes_processed += header.read_bit_mask(bytes_read[num_bytes_processed:])

    header.print_header_info()
    if header.isValid() is False:
        print "Header not valid, aborting"
        return

    #read full color image
    imageFullColor = RSBImage()
    num_bytes_processed += imageFullColor.read_image(header.width, header.height, header.calculate_bytes_per_pixel(), bytes_read[num_bytes_processed:])

    #create and save png from 256 color image
    if image256 is not None:
        newImg1 = Image.new('RGBA', (header.width, header.height))
        pixels = newImg1.load()
        for x in range(newImg1.size[0]):    # for every col:
            for y in range(newImg1.size[1]):    # For every row
                pixel_index = header.width * y + x
                pixel_data = image256.get_pixel(pixel_index)
                pixel_color = palette.get_color(ord(pixel_data))
                #alpha is ignored as it caused fully invisible PNGs
                pixels[x,y] = (pixel_color[0], pixel_color[1], pixel_color[2], 255) # set the colour accordingly, ignoring alpha
                
        newFilename = filename.replace(".RSB", "-256.PNG")
        newFilename = newFilename.replace(".rsb", "-256.PNG")
        newImg1.save(newFilename, "PNG")

    #create and save png from full color image
    newImg2 = Image.new('RGBA', (header.width, header.height))
    pixels = newImg2.load()
    for x in range(newImg2.size[0]):    # for every col:
        for y in range(newImg2.size[1]):    # For every row
            pixel_index = header.width * y + x
            pixel_data = imageFullColor.get_pixel(pixel_index)
            pixel_color = read_bitmask_RGBA_color(pixel_data, header.bitDepthRed, header.bitDepthGreen, header.bitDepthBlue, header.bitDepthAlpha)
            pixels[x,y] = (pixel_color[0], pixel_color[1], pixel_color[2], pixel_color[3]) # set the colour accordingly, ignoring alpha
    newFilename = filename.replace(".RSB", ".PNG")
    newFilename = newFilename.replace(".rsb", ".PNG")
    newImg2.save(newFilename, "PNG")

    #save meta data to JSON file
    newFilename = newFilename.replace(".PNG", ".JSON")
    meta = BinaryConversionUtilities.MetaInfo()
    meta.setFilename(os.path.basename(filename))
    meta.add_info("header", header)
    meta.writeJSON(newFilename)

    print "Processed: " + str(num_bytes_processed) + " bytes"
    print "Length: " + str(len(bytes_read)) + " bytes"
    print "Unprocessed: " + str(len(bytes_read) - num_bytes_processed) + " bytes"
    print "Finished converting: " + filename
    print ""

def processAllFilesInFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            #print(os.path.join(root, name))
            if name.upper().endswith(".RSB"):
                convert_RSB(join(root, name))
        for name in dirs:
            print("Walking directory: " + os.path.join(root, name))

    print "Finished processing all data in folder"
    print ""
    return

def main():
    """Main function that converts test data files"""
    processAllFilesInFolder("Data/Test")
    return
    processAllFilesInFolder("Data/R6")
    processAllFilesInFolder("Data/RSDemo")

if __name__ == "__main__":
    main()
