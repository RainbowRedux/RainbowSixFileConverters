"""Provides classes that will read and parse RSB Image files."""
import PIL
from FileUtilities.BinaryConversionUtilities import read_bitmask_ARGB_color, BinaryFileDataStructure, FileFormatReader

class RSBImageFile(FileFormatReader):
    """Class to read full RSB files"""
    def __init__(self):
        super(RSBImageFile, self).__init__()
        self.header = None
        self.image256 = None
        self.imageFullColor = None

    def read_data(self):
        super().read_data()

        fileReader = self._filereader

        #read header
        self.header = RSBHeader()
        self.header.read(fileReader)

        self.image256 = None
        if self.header.version == 0 and self.header.containsPalette == 1:
            #read palette
            self.palette = RSBPalette()
            self.palette.read(fileReader)

            #read 256 color image
            self.image256 = RSBImage()
            bytesPerPixel = 1
            self.image256.read_image(self.header.width, self.header.height, bytesPerPixel, fileReader)

        #in version 0 files, the bit mask is stored after the palette version of the image
        if self.header.version == 0:
            self.header.read_bit_mask(fileReader)

        if self.header.is_valid() is False:
            print("Header not valid, aborting")
            return

        #read full color image
        self.imageFullColor = RSBImage()
        self.imageFullColor.read_image(self.header.width, self.header.height, self.header.calculate_bytes_per_pixel(), fileReader)

    def convert_palette_image(self):
        """Converts the stored palettized version of the image into a full color RGBA image"""
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
        """Converts the stored "full color" version of the image into a full color RGBA image with 8bpp"""
        newImage = PIL.Image.new('RGBA', (self.header.width, self.header.height))
        pixels = newImage.load()
        for x in range(newImage.size[0]):    # for every col:
            for y in range(newImage.size[1]):    # For every row
                pixel_index = self.header.width * y + x
                pixel_data = self.imageFullColor.get_pixel(pixel_index)
                pixel_color = read_bitmask_ARGB_color(pixel_data, self.header.bitDepthRed, self.header.bitDepthGreen, self.header.bitDepthBlue, self.header.bitDepthAlpha)
                pixels[x,y] = (pixel_color[0], pixel_color[1], pixel_color[2], pixel_color[3]) # set the colour accordingly
        return newImage

    def check_color_key(self, imageColor, colorKey, bitmask, verbose=False):
        """Checks if the image color matches the colorkey. Fuzzy match based on the precision allowed by the bitmask"""
        #TODO: Improve matching
        bMatched = True
        if verbose:
            print("==NewColorComparison==")
        for i in range(len(imageColor)):
            elKey = colorKey[i]
            elCol = imageColor[i]
            elMaxValue = (2 ** bitmask[i]) - 1
            bitmaskPrecision = (1 / elMaxValue) * 255
            elKeyFactor = elKey / bitmaskPrecision
            elKeyMin = int(int(elKeyFactor) * bitmaskPrecision)
            elKeyMax = int(round((int(elKeyFactor) + 1) * bitmaskPrecision))

            if verbose:
                print("elKey: " + str(elKey))
                print("elCol: " + str(elCol))
                print("bitmaskPrecision: " + str(bitmaskPrecision))
                print("elKeyMin: " + str(elKeyMin))
                print("elKeyMax: " + str(elKeyMax))

            if elCol < elKeyMin or elCol > elKeyMax:
                bMatched = False
        return bMatched

    def convert_full_color_image_with_colorkey_mask(self, colorkeyRGB, verbose=False):
        """Converts the stored "full color" version of the image into a full color RGBA image with 8bpp
        colorkeyRGB can be a list or tuple"""
        newImage = self.convert_full_color_image()
        imageWidth, imageHeight = newImage.size
        pixdata = newImage.load()

        colorKey = list(colorkeyRGB)
        colorKeyWithAlpha = colorKey.copy()
        colorKeyWithAlpha.append(0)
        colorKeyWithAlpha = tuple(colorKeyWithAlpha)
        bitmask = self.header.get_rgba_bitmask_tuple()
        for y in range(imageHeight):
            for x in range(imageWidth):
                if self.check_color_key(pixdata[x, y][:3], colorKey, bitmask, verbose):
                    pixdata[x, y] = colorKeyWithAlpha

        return newImage


class RSBHeader(BinaryFileDataStructure):
    """Reads and stores information in the header of RSB files"""
    def __init__(self):
        super(RSBHeader, self).__init__()
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
        #Pylint disabled R1705 because stylistically i prefer this way here so i can extend it easier
        if self.isDXT: # pylint: disable=R1705
            if self.dxtType == 0: # pylint: disable=R1705
                return 1
            else:
                return 2
        else:
            bitDepthTotal = self.bitDepthRed + self.bitDepthGreen + self.bitDepthBlue + self.bitDepthAlpha
            return bitDepthTotal // 8

    def read_bit_mask(self, filereader):
        """Reads the bitmask for each color channel. May be stored outside of the header in Version 0 files"""
        #bit depth information
        self.bitDepthRed = filereader.read_uint()
        self.bitDepthGreen = filereader.read_uint()
        self.bitDepthBlue = filereader.read_uint()
        self.bitDepthAlpha = filereader.read_uint()

    def get_rgba_bitmask_tuple(self):
        """Returns the bitmask in RGBA order as a tuple"""
        return (self.bitDepthRed, self.bitDepthGreen, self.bitDepthBlue, self.bitDepthAlpha)

    def read(self, filereader):
        super().read(filereader)

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


class RSBPalette(BinaryFileDataStructure):
    """Reads and stores the color palette of version 0 files"""
    def __init__(self):
        super(RSBPalette, self).__init__()
        self.num_palette_entries = 256
        self.palette_entries = []

    def get_color(self, index):
        """Retrieves the color stored at the index"""
        return self.palette_entries[index]

    def print_palette(self):
        """Debug function to print all colors stored in the palette"""
        for color in self.palette_entries:
            print("R: " + str(color[0]) + "\tG: " + str(color[1]) + "\tB: " + str(color[2]) + "\tA: " + str(color[3]))

    def read(self, filereader):
        super().read(filereader)

        num_bytes_processed = 0
        self.palette_entries = []
        for _ in range(self.num_palette_entries):
            temp = filereader.read_bgra_color_8bpp_byte()
            num_bytes_processed += 4
            self.palette_entries.append(temp)
        return num_bytes_processed

class RSBImage(BinaryFileDataStructure):
    """Reads and stores the image data of RSB files"""
    def __init__(self):
        super(RSBImage, self).__init__()
        self.image = []

    def get_pixel(self, index):
        """Retrieves the pixel stored at the specified index"""
        if index >= len(self.image):
            print("Invalid index: " + str(index))
            return "0"
        return self.image[index]

    def read(self, filereader):
        super().read(filereader)
        print("Error! This class does not support the base read operation as it requires extra parameters")

    def read_image(self, width, height, bytes_per_pixel, filereader):
        """Reads data from the file that is to be interpreted as an image. Size of data read is determined by resolution and bytes per pixel. Image is not converted to RGBA image here, as the data can be a number of internal formats"""
        self.image = []
        for _ in range(width*height):
            self.image.append(filereader.read_bytes(bytes_per_pixel))
