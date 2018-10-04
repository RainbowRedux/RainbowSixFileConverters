import PIL
from  RainbowFileReaders import BinaryConversionUtilities
from BinaryConversionUtilities import read_bitmask_ARGB_color

class RSBImageFile(object):
    """Class to read full RSB files"""
    def __init__(self):
        pass
    
    def read_RSB(self, filename):
        imagefile = BinaryConversionUtilities.BinaryFileReader(filename)

        #read header
        self.header = RSBHeader()
        self.header.read_header(imagefile)

        self.image256 = None
        if self.header.version == 0 and self.header.containsPalette == 1:
            #read palette
            self.palette = RSBPalette()
            self.palette.read_palette(imagefile)

            #read 256 color image
            self.image256 = RSBImage()
            bytesPerPixel = 1
            self.image256.read_image(self.header.width, self.header.height, bytesPerPixel, imagefile)

        #in version 0 files, the bit mask is stored after the palette version of the image
        if self.header.version == 0:
            self.header.read_bit_mask(imagefile)

        if self.header.is_valid() is False:
            print("Header not valid, aborting")
            return
        
        #read full color image
        self.imageFullColor = RSBImage()
        self.imageFullColor.read_image(self.header.width, self.header.height, self.header.calculate_bytes_per_pixel(), imagefile)

        print("Processed: " + str(imagefile.get_seekg()) + " bytes")
        print("Length: " + str(imagefile.get_length()) + " bytes")
        print("Unprocessed: " + str(imagefile.get_length() - imagefile.get_seekg()) + " bytes")

    def convert_palette_image(self):
        newImage = PIL.Image.new('RGBA', (self.header.width, self.header.height))
        pixels = newImage.load()
        for x in range(newImage.size[0]):    # for every col:
            for y in range(newImage.size[1]):    # For every row
                pixel_index = self.header.width * y + x
                pixel_data = self.image256.get_pixel(pixel_index)
                pixel_color = self.palette.get_color(ord(pixel_data))
                #alpha is ignored as it caused fully invisible PNGs
                pixels[x,y] = (pixel_color[0], pixel_color[1], pixel_color[2], 255) # set the colour accordingly, ignoring alpha
        return newImage
                

    def convert_full_color_image(self):
        newImage = PIL.Image.new('RGBA', (self.header.width, self.header.height))
        pixels = newImage.load()
        for x in range(newImage.size[0]):    # for every col:
            for y in range(newImage.size[1]):    # For every row
                pixel_index = self.header.width * y + x
                pixel_data = self.imageFullColor.get_pixel(pixel_index)
                pixel_color = read_bitmask_ARGB_color(pixel_data, self.header.bitDepthRed, self.header.bitDepthGreen, self.header.bitDepthBlue, self.header.bitDepthAlpha)
                pixels[x,y] = (pixel_color[0], pixel_color[1], pixel_color[2], pixel_color[3]) # set the colour accordingly
        return newImage
    

class RSBHeader(object):
    """Reads and stores information in the header of RSB files"""
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

    def is_valid(self):
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
            return bitDepthTotal // 8

    def print_header_info(self):
        print("RSB Version: " + str(self.version))
        print("Image Width: " + str(self.width))
        print("Image height: " + str(self.height))
        if self.bitDepthAlpha > 0:
            print("Has Alpha?: True")
        else:
            print("Has Alpha?: False")
        print("BitDepthRed: " + str(self.bitDepthRed))
        print("BitDepthGreen: " + str(self.bitDepthGreen))
        print("BitDepthBlue: " + str(self.bitDepthBlue))
        print("BitDepthAlpha: " + str(self.bitDepthAlpha))
        print("containsPalette: " + str(self.containsPalette))
        print("Unknown var2: " + str(self.unknown2))
        print("Unknown var3: " + str(self.unknown3))
        print("Unknown var4: " + str(self.unknown4))
        print("Unknown var5: " + str(self.unknown5))
        print("isDXT: " + str(self.isDXT))
        print("DXT Type: " + str(self.dxtType))

    def read_bit_mask(self, filereader):
        """Reads the bitmask for each color channel. May be stored outside of the header in Version 0 files"""
        #bit depth information
        self.bitDepthRed = filereader.read_uint()
        self.bitDepthGreen = filereader.read_uint()
        self.bitDepthBlue = filereader.read_uint()
        self.bitDepthAlpha = filereader.read_uint()

    def read_header(self, filereader):
        self.version = filereader.read_uint()
        self.width = filereader.read_uint()
        self.height = filereader.read_uint()

        if self.version == 0:
            self.containsPalette = filereader.read_uint()

        #num_bytes_processed += 1
        if self.version > 7:
            #process 3 more variables
            self.unknown2 = filereader.read_uint()
            self.unknown3 = filereader.read_uint()
            self.unknown4 = filereader.read_bytes(1)

        if self.version > 0:
            #bit depth information
            self.read_bit_mask(filereader)

        if self.version >= 9: 
            self.unknown5 = filereader.read_uint()

            self.dxtType = filereader.read_uint()
            if self.dxtType >= 0 and self.dxtType < 5:
                self.isDXT = True


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
            print("R: " + str(color[0]) + "\tG: " + str(color[1]) + "\tB: " + str(color[2]) + "\tA: " + str(color[3]))

    def read_palette(self, filereader):
        num_bytes_processed = 0
        self.palette_entries = []
        for i in range(self.num_palette_entries):
            temp = filereader.read_bgra_color_8bpp_byte()
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
            print("Invalid index: " + str(index))
            return "0"
        return self.image[index]

    def read_image(self, width, height, bytes_per_pixel, filereader):
        self.image = []
        for i in range(width*height):
            self.image.append(filereader.read_bytes(bytes_per_pixel))
