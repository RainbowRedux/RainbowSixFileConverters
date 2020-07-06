"""
Provides some utility classes and functions for reading data from binary files
Also provides some functions to unpack data from packed structures
"""
import struct
import logging

from typing import List, Tuple

from deprecated import deprecated # type: ignore

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

    def open_file(self, path: str):
        """Opens the file at specified path and reads all data at once into buffer self.bytes"""
        self.filepath = path
        log.debug("Opening file for read: %s", self.filepath)
        f = open(path, "rb")
        # read entire file
        self.bytes = f.read()
        f.close()

        # note that we "seek" to the beginning of the file at load
        self._seekg = 0

    def read_bytes(self, size: int) -> bytes:
        """Reads and returns a sequence of bytes of specified length"""
        if len(self.bytes) < self._seekg + size:
            log.critical("File not long enough to read %d bytes", str(size))
            raise ValueError("File not long enough to read " + str(size) + " bytes")
        val = self.bytes[self._seekg:self._seekg+size]
        self._seekg += size
        return val

    @deprecated
    def read_uint(self) -> int:
        """Converts 4 bytes to an integer"""
        return self.read_uint32()

    def read_uint32(self) -> int:
        """Converts 4 bytes to an integer"""
        #https://stackoverflow.com/a/444610
        data = self.read_bytes(4)
        if len(data) < 4:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<I", data)[0]

    @deprecated
    def read_int(self) -> int:
        """Converts 4 bytes to an integer"""
        return self.read_int32()

    def read_int32(self) -> int:
        """Converts 4 bytes to an integer"""
        #https://stackoverflow.com/a/444610
        data = self.read_bytes(4)
        if len(data) < 4:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<i", data)[0]

    @deprecated
    def read_short_int(self) -> int:
        """Converts 2 bytes to a short integer"""
        return self.read_int16()

    def read_int16(self) -> int:
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<H", data)[0]

    @deprecated
    def read_short_uint(self) -> int:
        """Converts 2 bytes to a short integer"""
        return self.read_uint16()

    def read_uint16(self) -> int:
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("<h", data)[0]

    def read_float(self) -> float:
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(4)
        if len(data) < 4:
            log.error("Data read not long enough, returning 0")
            return 0
        return struct.unpack("f", data)[0]

    def read_vec_f(self, size: int) -> List[float]:
        """Reads a specified number of floats into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_float())
        return vec

    @deprecated
    def read_vec_uint(self, size: int) -> List[int]:
        """Reads a specified number of uints into a list"""
        return self.read_vec_uint32(size)

    def read_vec_uint32(self, size: int) -> List[int]:
        """Reads a specified number of uints into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_uint32())
        return vec

    @deprecated
    def read_vec_short_uint(self, size: int) -> List[int]:
        """Reads a specified number of short uints into a list"""
        return self.read_vec_uint16(size)

    def read_vec_uint16(self, size: int) -> List[int]:
        """Reads a specified number of short uints into a list"""
        vec = []
        for _ in range(size):
            vec.append(self.read_uint16())
        return vec

    def read_bgra_color_8bpp_byte(self) -> List[int]:
        """reads 4 bytes into a BGRA color, and then converts to RGBA."""
        byteStream = self.read_bytes(4)
        color: List[int] = []
        for j in range(4):
            color.append(ord(byteStream[j:j + 1]))
        tempblue = color[0]
        color[0] = color[2]
        color[2] = tempblue
        return color

    def read_rgb_color_24bpp_uint(self) -> List[int]:
        """Reads 3 uints"""
        color = []
        for _ in range(3):
            color.append(self.read_uint32())
        return color

    def read_rgba_color_32bpp_uint(self) -> List[int]:
        """Reads 4 uints"""
        color = []
        for _ in range(4):
            color.append(self.read_uint32())
        return color

    def read_rgba_color_32bpp_float(self) -> List[float]:
        """Reads 4 uints"""
        color = []
        for _ in range(4):
            color.append(self.read_float())
        return color

    def get_length(self) -> int:
        """Returns the length of the file that was read"""
        return len(self.bytes)

    def get_seekg(self) -> int:
        """Returns the current location that is due to be read next operation"""
        return self._seekg

    def is_at_eof(self) -> bool:
        """Returns true if all bytes have been read, more specifically if seekg >= length of bytes"""
        return self.get_seekg() >= self.get_length()


class FileFormatReader(object):
    """A helper class that provides a common interface for all file formats
    Provides utility methods to print detailed information on class
    Child classes just need to specify fields to perform detailed read operations in read_data"""
    def __init__(self):
        super(FileFormatReader, self).__init__()
        self.filepath: str = None
        self._filereader: BinaryFileReader = None
        self.verboseOutput: bool = False

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

    def read(self, filereader: BinaryFileReader):
        """This is to be overriden in child classes. This is where all data for this structure can be read from"""

    def print_structure_info(self):
        """Helper method to output class information for debugging"""
        log_pprint(vars(self), logging.INFO)

class SizedCString(object):
    """Reads a null-terminated string from a file. Assumes there is a 4 byte integer specifying size"""
    def __init__(self, filereader: BinaryFileReader = None):
        self.string_length: int = -1
        self.string_value_raw: bytes = b''
        self.string: str = ""

        if filereader:
            self.read(filereader)

    def read(self, filereader: BinaryFileReader):
        """Reads a length and then a null-terminated string of that length from the BinaryFileReader"""
        self.string_length = filereader.read_uint32()
        self.string_value_raw = filereader.read_bytes(self.string_length)
        self.string = self.string_value_raw[:-1].decode("utf-8")


def bytes_to_shortint(byteStream: bytes) -> Tuple[int]:
    """Converts 2 bytes to a short integer"""
    # Ignore this in typing, as the 'H' will guarantee ints are returned
    return struct.unpack('H', byteStream) # type: ignore
