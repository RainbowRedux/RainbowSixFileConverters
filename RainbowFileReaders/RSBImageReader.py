"""Provides classes that will read and parse RSB Image files."""
import logging

from typing import Optional, Tuple, List

from PIL import Image as PILImage # type: ignore
from PIL import ImagePalette # type: ignore
from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader, bytes_to_shortint, BinaryFileReader
from FileUtilities.ColorConversionUtilities import get_color_format, get_color_lookup_table
from RainbowFileReaders.MathHelpers import IntIterable

log = logging.getLogger(__name__)

class RSBImageFile(FileFormatReader):
    """Class to read full RSB files"""
    def __init__(self):
        super(RSBImageFile, self).__init__()
        self.header: RSBHeader = RSBHeader()
        self.image256: Optional[RSBImage] = None
        self.imageFullColor: RSBImage = RSBImage()

    def read_data(self):
        """Reads the data from an RSB Image file. Overrides parent function"""
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
            log.critical("Header not valid, aborting")
            return

        #read full color image
        self.imageFullColor = RSBImage()
        self.imageFullColor.read_image(self.header.width, self.header.height, self.header.calculate_bytes_per_pixel(), fileReader)

    def convert_palette_image(self) -> Optional[PILImage.Image]:
        """
        Converts the stored palettized version of the image into a full color RGBA image
        If a palette image exists, a full color RGBA image will be returned
        If no palette image exists, None is returned
        """
        if self.image256 is None:
            return None
        newImage = PILImage.new('RGBA', (self.header.width, self.header.height))
        pixels = newImage.load()
        for x in range(newImage.size[0]):    # for every col:
            for y in range(newImage.size[1]):    # For every row
                pixel_index = self.header.width * y + x
                pixel_data = self.image256.get_pixel(pixel_index)
                pixel_color = self.palette.get_color(ord(pixel_data))
                #alpha is ignored as it caused fully invisible PNGs
                pixels[x,y] = (pixel_color[0], pixel_color[1], pixel_color[2], 255) # set the colour accordingly, ignoring alpha
        return newImage

    def convert_palette_image_pil_palette(self) -> Optional[PILImage.Image]:
        """
        Converts the stored palettized version of the image into a full color RGBA image
        If a palette image exists, a palette based PIL image will be returned
        If no palette image exists, None is returned
        """
        if self.image256 is None:
            return None
        log.debug("Palette conversion pending")
        newImage = PILImage.new('P', (self.header.width, self.header.height))

        newPalette = ImagePalette.ImagePalette(mode='RGBA')
        for index, color in enumerate(self.palette.palette_entries):
            newColorTuple = tuple(color[:3])
            newPalette.colors[newColorTuple] = index
            newPalette.palette[index] = newColorTuple[0]
            newPalette.palette[index+256] = newColorTuple[1]
            newPalette.palette[index+512] = newColorTuple[2]
            newPalette.palette[index+768] = 128
        newPalette.dirty = 1

        imageData = []
        for data in self.image256.image:
            imageData.append(ord(data))
        newImage.putdata(imageData)
        newImage.palette = newPalette

        return newImage


    def convert_full_color_image(self, force_alpha_channel: bool = False) -> PILImage.Image:
        """
        Converts the stored "full color" version of the image into a full color RGBA image with 8bpp
        An alpha channel will only be generated if alpha information exists, or force_alpha_channel is True
        """
        pixelformat = 'RGB'
        if self.header.bitDepthAlpha != 0 or force_alpha_channel:
            pixelformat = 'RGBA'

        color_format = get_color_format(self.header.bitDepthRed, self.header.bitDepthGreen, self.header.bitDepthBlue, self.header.bitDepthAlpha)
        color_lookup = get_color_lookup_table(color_format)
        newImage = PILImage.new(pixelformat, (self.header.width, self.header.height))
        pixels = newImage.load()
        for x in range(newImage.size[0]):    # for every col:
            for y in range(newImage.size[1]):    # For every row
                pixel_index = self.header.width * y + x
                pixel_data = self.imageFullColor.image[pixel_index]
                pixel_color_16 = bytes_to_shortint(pixel_data)[0]
                pixel_color = color_lookup[pixel_color_16]
                if self.header.bitDepthAlpha == 0:
                    #strip alpha channel if not required
                    pixel_color = pixel_color[:3]
                pixels[x,y] = tuple(pixel_color) # set the colour accordingly

        return newImage

    def check_color_key(self, imageColor: IntIterable, colorKey: IntIterable, bitmask: IntIterable) -> bool:
        """Checks if the image color matches the colorkey. Fuzzy match based on the precision allowed by the bitmask"""
        #TODO: Improve matching
        bMatched = True
        log.debug("==NewColorComparison==")
        # pylint: disable=consider-using-enumerate
        for i in range(len(imageColor)):
            elKey = colorKey[i]
            elCol = imageColor[i]
            elMaxValue = (2 ** bitmask[i]) - 1
            bitmaskPrecision = (1 / elMaxValue) * 255
            elKeyFactor = elKey / bitmaskPrecision
            elKeyMin = int(int(elKeyFactor) * bitmaskPrecision)
            elKeyMax = int(round((int(elKeyFactor) + 1) * bitmaskPrecision))

            log.debug("elKey: %s", str(elKey))
            log.debug("elCol: %s", str(elCol))
            log.debug("bitmaskPrecision: %s", str(bitmaskPrecision))
            log.debug("elKeyMin: %s", str(elKeyMin))
            log.debug("elKeyMax: %s", str(elKeyMax))

            #elKeyMin is actually from the range before generally speaking. In the case of a white key, elKeyMin and elKeyMax will match, so special case handling required.
            if elCol <= elKeyMin or elCol > elKeyMax:
                if elCol == elKey and elKey == 255:
                    pass
                elif elCol == elKey and elKey == 0:
                    pass
                else:
                    bMatched = False
        return bMatched

    def convert_full_color_image_with_colorkey_mask(self, colorkeyRGB: IntIterable) -> PILImage.Image:
        """Converts the stored "full color" version of the image into a full color RGBA image with 8bpp
        colorkeyRGB can be a list or tuple"""
        if colorkeyRGB is None:
            return self.convert_full_color_image()

        newImage = self.convert_full_color_image(force_alpha_channel=True)
        imageWidth, imageHeight = newImage.size
        pixdata = newImage.load()

        colorKey = list(colorkeyRGB)
        colorKeyCopy = colorKey.copy()
        colorKeyCopy.append(0)
        colorKeyWithAlpha = tuple(colorKeyCopy)
        bitmask = self.header.get_rgba_bitmask_tuple()
        for y in range(imageHeight):
            for x in range(imageWidth):
                if self.check_color_key(pixdata[x, y][:3], colorKey, bitmask):
                    pixdata[x, y] = colorKeyWithAlpha

        return newImage


class RSBHeader(BinaryFileDataStructure):
    """Reads and stores information in the header of RSB files"""
    def __init__(self):
        super(RSBHeader, self).__init__()
        self.version: int = None
        self.width: int = None
        self.height: int = None
        self.containsPaletteRaw: int = None
        self.unknown2: int = None
        self.unknown3: int = None
        self.unknown4: bytes = None
        self.unknown5: int = None
        self.bitDepthRed: int = None
        self.bitDepthGreen: int = None
        self.bitDepthBlue: int = None
        self.bitDepthAlpha: int = None
        self.isDXT: bool = False
        self.dxtType: int = None

    def is_valid(self) -> bool:
        """Some images cause errors when converting, they seem to have invalid headers. Simple checks here identify bad headers"""
        if self.bitDepthAlpha + self.bitDepthBlue + self.bitDepthGreen + self.bitDepthRed == 0:
            return False
        if self.bitDepthAlpha + self.bitDepthBlue + self.bitDepthGreen + self.bitDepthRed > 32:
            return False
        return True

    def calculate_bytes_per_pixel(self) -> int:
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

    def read_bit_mask(self, filereader: BinaryFileReader):
        """Reads the bitmask for each color channel. May be stored outside of the header in Version 0 files"""
        #bit depth information
        self.bitDepthRed = filereader.read_uint32()
        self.bitDepthGreen = filereader.read_uint32()
        self.bitDepthBlue = filereader.read_uint32()
        self.bitDepthAlpha = filereader.read_uint32()

    def get_rgba_bitmask_tuple(self) -> Tuple[int, ...]:
        """Returns the bitmask in RGBA order as a tuple"""
        return (self.bitDepthRed, self.bitDepthGreen, self.bitDepthBlue, self.bitDepthAlpha)

    def read(self, filereader: BinaryFileReader):
        """Reads the data from an RSB header. Overrides parent function"""
        super().read(filereader)

        self.version = filereader.read_uint32()
        self.width = filereader.read_uint32()
        self.height = filereader.read_uint32()

        if self.version == 0:
            self.containsPaletteRaw = filereader.read_uint32()
            if self.containsPaletteRaw == 1:
                self.containsPalette = True
            else:
                self.containsPalette = False

        #num_bytes_processed += 1
        if self.version > 7:
            #process 3 more variables
            self.unknown2 = filereader.read_uint32()
            self.unknown3 = filereader.read_uint32()
            self.unknown4 = filereader.read_bytes(1)

        if self.version > 0:
            #bit depth information
            self.read_bit_mask(filereader)

        if self.version >= 9:
            self.unknown5 = filereader.read_uint32()

            self.dxtType = filereader.read_uint32()
            if self.dxtType >= 0 and self.dxtType < 5:
                self.isDXT = True


class RSBPalette(BinaryFileDataStructure):
    """Reads and stores the color palette of version 0 files"""
    def __init__(self):
        super(RSBPalette, self).__init__()
        self.num_palette_entries = 256
        self.palette_entries: List[List[int]] = []

    def get_color(self, index: int) -> List[int]:
        """Retrieves the color stored at the index"""
        return self.palette_entries[index]

    def print_palette(self):
        """Debug function to print all colors stored in the palette"""
        for i, color in enumerate(self.palette_entries):
            log.info("I: %d (R: %d\tG: %d\tB: %d\tA: %d)", i, color[0], color[1], color[2], color[3])

    def read(self, filereader: BinaryFileReader):
        """Reads data associated with an RSBPalette"""
        super().read(filereader)

        self.palette_entries = []
        for _ in range(self.num_palette_entries):
            temp = filereader.read_bgra_color_8bpp_byte()
            self.palette_entries.append(temp)

class RSBImage(BinaryFileDataStructure):
    """Reads and stores the image data of RSB files"""
    def __init__(self):
        super(RSBImage, self).__init__()
        self.image: List[bytes] = []

    def get_pixel(self, index: int) -> bytes:
        """Retrieves the pixel stored at the specified index"""
        if index >= len(self.image):
            log.error("Invalid index: %d", index)
            return b'0'
        return self.image[index]

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)
        log.error("Error! This class does not support the base read operation as it requires extra parameters")

    def read_image(self, width: int, height: int, bytes_per_pixel: int, filereader: BinaryFileReader):
        """Reads data from the file that is to be interpreted as an image. Size of data read is determined by resolution and bytes per pixel. Image is not converted to RGBA image here, as the data can be a number of internal formats"""
        self.image = []
        for _ in range(width*height):
            self.image.append(filereader.read_bytes(bytes_per_pixel))
