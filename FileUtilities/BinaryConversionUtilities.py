"""
Provides some utility classes and functions for reading data from binary files
Also provides some functions to unpack data from packed structures
"""
import struct
import pprint

from math import ceil, floor

class BinaryFileReader(object):
    """A wrapper for reading and conversion operations on binary file data."""
    def __init__(self, path=None):
        super(BinaryFileReader, self).__init__()
        if path is not None:
            self.openFile(path)

    def openFile(self, path):
        """Opens the file at specified path and reads all data at once into buffer self.bytes"""
        #read entire file
        f = open(path, "rb")
        self.bytes = f.read()
        self._seekg = 0
        f.close()

    def read_bytes(self, size):
        """Converts 2 bytes to a short integer"""
        if len(self.bytes) < self._seekg + size:
            raise ValueError("File not long enough to read " + str(size) + " bytes")
        val = self.bytes[self._seekg:self._seekg+size]
        self._seekg += size
        return val

    def read_uint(self):
        """Converts 4 bytes to an integer"""
        #https://stackoverflow.com/a/444610
        data = self.read_bytes(4)
        if len(data) < 4:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<I", data)[0]

    def read_int(self):
        """Converts 4 bytes to an integer"""
        #https://stackoverflow.com/a/444610
        data = self.read_bytes(4)
        if len(data) < 4:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<i", data)[0]

    def read_short_int(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<H", data)[0]

    def read_short_uint(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<h", data)[0]

    def read_float(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(4)
        if len(data) < 4:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("f", data)[0]

    def read_vec_f(self, size):
        """Reads a specified number of floats into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_float())
        return vec

    def read_vec_uint(self, size):
        """Reads a specified number of uints into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_uint())
        return vec

    def read_vec_short_uint(self, size):
        """Reads a specified number of short uints into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_short_uint())
        return vec

    def read_bgra_color_8bpp_byte(self):
        """reads 4 bytes into a BGRA color, and then converts to RGBA."""
        byteStream = self.read_bytes(4)
        color = []
        for j in range(4):
            color.append(ord(byteStream[j:j + 1]))
        tempblue = color[0]
        color[0] = color[2]
        color[2] = tempblue
        return color

    def read_rgb_color_24bpp_uint(self):
        """Reads 3 uints"""
        color = []
        for _ in range(3):
            color.append(self.read_uint())
        return color

    def read_rgba_color_32bpp_uint(self):
        """Reads 4 uints"""
        color = []
        for _ in range(4):
            color.append(self.read_uint())
        return color

    def read_rgba_color_32bpp_float(self):
        """Reads 4 uints"""
        color = []
        for _ in range(4):
            color.append(self.read_float())
        return color

    def get_length(self):
        """Returns the length of the file that was read"""
        return len(self.bytes)

    def get_seekg(self):
        """Returns the current location that is due to be read next operation"""
        return self._seekg

class FileFormatReader(object):
    """A helper class that provides a common interface for all file formats
    Provides utility methods to print detailed information on class
    Child classes just need to specify fields to perform detailed read operations in read_data"""
    def __init__(self):
        super(FileFormatReader, self).__init__()
        self.filepath = None

    def print_structure_info(self):
        """Utility method to print detailed information on data stored"""
        pprint.pprint(vars(self))

    def read_file(self, filepath, verboseOutput=False):
        """Reads the file specified into memory and then will call read_data to process"""
        #TODO: Add error checking to see if this file was loaded
        self.filepath = filepath
        self.verboseOutput = verboseOutput
        if self.verboseOutput:
            print("== Processing: " + str(self.filepath))
        self._filereader = BinaryFileReader(filepath)

        self.read_data()

        if self.verboseOutput:
            print("== Finished Processing: " + str(self.filepath))
            print("Processed: " + str(self._filereader.get_seekg()) + " bytes")
            print("Length: " + str(self._filereader.get_length()) + " bytes")
            print("Unprocessed: " + str(self._filereader.get_length() - self._filereader.get_seekg()) + " bytes")

        del self._filereader
        self._filereader = None

    def read_data(self):
        """The method to override with detailed data processing"""
        pass


class BinaryFileDataStructure(object):
    """A helper class to provide utility methods and a common interface to data structures"""
    def __init__(self):
        super().__init__()

    def read_section_string(self, filereader):
        """Read a string that stores the name of this section - header related"""
        self.read_named_string(filereader, "sectionString")

    def read_name_string(self, filereader):
        """Read a string for the name of this object"""
        self.read_named_string(filereader, "nameString")

    def read_version_string(self, filereader):
        """Read the string for the version. Does not read associated version numbers"""
        self.read_named_string(filereader, "versionString")

    def read_named_string(self, filereader, stringName):
        """Read a string with the specified name"""
        newStringLength = filereader.read_uint()
        newStringRaw = filereader.read_bytes(newStringLength)
        newString = newStringRaw[:-1].decode("utf-8")
        self.__setattr__(stringName + "Length", newStringLength)
        self.__setattr__(stringName + "Raw", newStringRaw)
        self.__setattr__(stringName, newString)

    def read(self, filereader):
        """This is to be overriden in child classes. This is where all data for this structure can be read from"""
        pass

    def print_structure_info(self):
        """Helper method to output class information for debugging"""
        pprint.pprint(vars(self))

def bytes_to_shortint(byteStream):
    """Converts 2 bytes to a short integer"""
    return struct.unpack('H', byteStream)

def isPowerOf2(number):
    """Checks if a number is a power of 2"""
    num1 = ((number & (number - 1)) == 0)
    return num1

import functools

@functools.lru_cache(maxsize=10)
def calc_bitmasks_ARGB_color(bdR, bdG, bdB, bdA):
    """Calculates the appropriate bitmasks for a color stored in ARGB format."""

    redMask = 0
    greenMask = 0
    blueMask = 0
    alphaMask = 0

    if bdA > 0:
        for _ in range(bdA):
            alphaMask = (alphaMask << 1) + 1
        alphaMask = alphaMask << (bdR + bdG + bdB)

    for _ in range(bdR):
        redMask = (redMask << 1) + 1
    redMask = redMask << (bdG + bdB)

    greenMask = 0
    for _ in range(bdG):
        greenMask = (greenMask << 1) + 1
    greenMask = greenMask << (bdB)

    blueMask = 0
    for _ in range(bdB):
        blueMask = (blueMask << 1) + 1

    masks = [redMask, greenMask, blueMask, alphaMask]
    return masks

@functools.lru_cache(maxsize=None)
def read_bitmask_ARGB_color(colorVal, bdR, bdG, bdB, bdA):
    """Reads an ARGB color with custom bit depths for each channel, returns in RGBA format"""
    masks = calc_bitmasks_ARGB_color(bdR, bdG, bdB, bdA)
    redMask = masks[0]
    greenMask = masks[1]
    blueMask = masks[2]
    alphaMask = masks[3]

    alphaColor = 255
    if bdA > 0:
        alphaColor = alphaMask & colorVal
        alphaColor = alphaColor >> (bdR + bdG + bdB)
        alphaMaxValue = 2 ** bdA - 1
        #convert to full 255 range of color
        alphaColor = float(alphaColor) / float(alphaMaxValue) * 255
        alphaColor = int(floor(alphaColor))

    redColor = redMask & colorVal
    redColor = redColor >> (bdG + bdB)
    redMaxValue = (2 ** bdR) - 1
    #convert to full 255 range of color
    redColor = float(redColor) / float(redMaxValue) * 255
    redColor = int(floor(redColor))

    greenColor = greenMask & colorVal
    greenColor = greenColor >> (bdB)
    greenMaxValue = (2 ** bdG) - 1
    #convert to full 255 range of color
    greenColor = float(greenColor) / float(greenMaxValue) * 255
    greenColor = int(floor(greenColor))

    blueColor = blueMask & colorVal
    blueMaxValue = (2 ** bdB) - 1
    #convert to full 255 range of color
    blueColor = float(blueColor) / float(blueMaxValue) * 255
    blueColor = int(floor(blueColor))

    return [redColor, greenColor, blueColor, alphaColor]
