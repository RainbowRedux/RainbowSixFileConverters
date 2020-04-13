"""
Provides some utility classes and functions for reading data from binary files
Also provides some functions to unpack data from packed structures
"""
import struct
import logging

import functools

from math import floor

from deprecated import deprecated

from FileUtilities.LoggingUtils import log_pprint

log = logging.getLogger(__name__)

# Disabling "Too many public methods", as this is caused by some deprecated wrapper
# functions that I don't want to remove just yet.
# pylint: disable=R0904
class BinaryFileReader(object):
    """
    A wrapper for reading and conversion operations on binary file data.
    All datatypes assume they were written in little-endian format
    """
    def __init__(self, path=None):
        super(BinaryFileReader, self).__init__()
        if path is not None:
            self.open_file(path)

    def open_file(self, path):
        """Opens the file at specified path and reads all data at once into buffer self.bytes"""
        self.filepath = path
        log.debug("Opening file for read: %s", self.filepath)
        f = open(path, "rb")
        # read entire file
        self.bytes = f.read()
        f.close()

        # note that we "seek" to the beginning of the file at load
        self._seekg = 0

    def read_bytes(self, size):
        """Reads and returns a sequence of bytes of specified length"""
        if len(self.bytes) < self._seekg + size:
            log.critical("File not long enough to read %d bytes", str(size))
            raise ValueError("File not long enough to read " + str(size) + " bytes")
        val = self.bytes[self._seekg:self._seekg+size]
        self._seekg += size
        return val

    @deprecated
    def read_uint(self):
        """Converts 4 bytes to an integer"""
        return self.read_uint32()

    def read_uint32(self):
        """Converts 4 bytes to an integer"""
        #https://stackoverflow.com/a/444610
        data = self.read_bytes(4)
        if len(data) < 4:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<I", data)[0]

    @deprecated
    def read_int(self):
        """Converts 4 bytes to an integer"""
        return self.read_int32()

    def read_int32(self):
        """Converts 4 bytes to an integer"""
        #https://stackoverflow.com/a/444610
        data = self.read_bytes(4)
        if len(data) < 4:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<i", data)[0]

    @deprecated
    def read_short_int(self):
        """Converts 2 bytes to a short integer"""
        return self.read_int16()

    def read_int16(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<H", data)[0]

    @deprecated
    def read_short_uint(self):
        """Converts 2 bytes to a short integer"""
        return self.read_uint16()

    def read_uint16(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<h", data)[0]

    def read_float(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(4)
        if len(data) < 4:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("f", data)[0]

    def read_vec_f(self, size):
        """Reads a specified number of floats into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_float())
        return vec

    @deprecated
    def read_vec_uint(self, size):
        """Reads a specified number of uints into a list"""
        return self.read_vec_uint32(size)

    def read_vec_uint32(self, size):
        """Reads a specified number of uints into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_uint32())
        return vec

    @deprecated
    def read_vec_short_uint(self, size):
        """Reads a specified number of short uints into a list"""
        return self.read_vec_uint16(size)

    def read_vec_uint16(self, size):
        """Reads a specified number of short uints into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_uint16())
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
            color.append(self.read_uint32())
        return color

    def read_rgba_color_32bpp_uint(self):
        """Reads 4 uints"""
        color = []
        for _ in range(4):
            color.append(self.read_uint32())
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

    def is_at_eof(self):
        """Returns true if all bytes have been read, more specifically if seekg >= length of bytes"""
        return self.get_seekg() >= self.get_length()


class FileFormatReader(object):
    """A helper class that provides a common interface for all file formats
    Provides utility methods to print detailed information on class
    Child classes just need to specify fields to perform detailed read operations in read_data"""
    def __init__(self):
        super(FileFormatReader, self).__init__()
        self.filepath = None

    def print_structure_info(self):
        """Utility method to print detailed information on data stored"""
        log_pprint(vars(self), logging.INFO)

    def read_file(self, filepath, verboseOutput=False):
        """Reads the file specified into memory and then will call read_data to process"""
        #TODO: Add error checking to see if this file was loaded
        self.filepath = filepath
        self.verboseOutput = verboseOutput

        log.debug("Processing: %s", self.filepath)
        self._filereader = BinaryFileReader(filepath)

        self.read_data()

        unprocessed_bytes = self._filereader.get_length() - self._filereader.get_seekg()
        if unprocessed_bytes > 0:
            log.warning("Didn't read the final %d bytes of file %s", unprocessed_bytes, self.filepath)

        log.debug("Finished Processing: %s", self.filepath)
        log.debug("Length: %d bytes", self._filereader.get_length())
        log.debug("Processed: %d bytes", self._filereader.get_seekg())
        log.debug("Unprocessed: %d bytes", self._filereader.get_length() - self._filereader.get_seekg())

        reachedEOF = self._filereader.is_at_eof()

        del self._filereader
        self._filereader = None

        return reachedEOF

    def read_data(self):
        """The method to override with detailed data processing"""


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
        newStringLength = filereader.read_uint32()
        newStringRaw = filereader.read_bytes(newStringLength)
        newString = newStringRaw[:-1].decode("utf-8")
        self.__setattr__(stringName + "Length", newStringLength)
        self.__setattr__(stringName + "Raw", newStringRaw)
        self.__setattr__(stringName, newString)

    def read(self, filereader):
        """This is to be overriden in child classes. This is where all data for this structure can be read from"""

    def print_structure_info(self):
        """Helper method to output class information for debugging"""
        log_pprint(vars(self), logging.INFO)

def bytes_to_shortint(byteStream):
    """Converts 2 bytes to a short integer"""
    return struct.unpack('H', byteStream)

@functools.lru_cache(maxsize=8)
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
