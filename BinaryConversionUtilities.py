import struct
import json

class BinaryFileReader(object):
    """A wrapper for reading and conversion operations on binary file data."""
    def __init__(self):
        super(BinaryFileReader, self).__init__()
    
    def __init__(self, path):
        super(BinaryFileReader, self).__init__()
        self.openFile(path)

    def openFile(self, path):
        #read entire file
        f = open(path, "rb")
        self.bytes = f.read()
        self._seekg = 0
        f.close()

    def read_bytes(self, size):
        """Converts 2 bytes to a short integer"""
        if len(self.bytes) < self._seekg + size:
            print("File not long enough, returning nothing")
            return []
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

    def read_shortint(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(2)
        if len(data) < 2:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("H", data)[0]

    def read_float(self):
        """Converts 2 bytes to a short integer"""
        data = self.read_bytes(4)
        if len(data) < 4:
            print("Data read not long enough, returning 0")
            return 0
        return struct.unpack("f", data)[0]

    def read_vec_f(self, size):
        vec = []
        for i in range(size):
            vec.append(self.read_float())
        return vec

    def read_vec_uint(self, size):
        vec = []
        for i in range(size):
            vec.append(self.read_uint())
        return vec
    
    def read_bgra_color_8bpp_byte(self):
        """reads 4 bytes into a BGRA color, and then converts to RGBA."""
        bytearray = self.read_bytes(4)
        color = []
        for j in range(4):
            color.append(ord(bytearray[j:j + 1]))
        tempblue = color[0]
        color[0] = color[2]
        color[2] = tempblue
        return color
    
    def read_rgb_color_32bpp_uint(self):
        """Reads 3 uints"""
        color = []
        for i in range(3):
            color.append(self.read_uint())
        return color
    
    def get_length(self):
        return len(self.bytes)

    def get_seekg(self):
        return self._seekg
        

def bytes_to_int(bytearray):
    """Converts 4 bytes to an integer"""
    #https://stackoverflow.com/a/444610
    if len(bytearray) < 4:
        return 0
    return struct.unpack("<i", bytearray[0:4])[0]

def bytes_to_uint(bytearray):
    """Converts 4 bytes to an integer"""
    #https://stackoverflow.com/a/444610
    if len(bytearray) < 4:
        return 0
    return struct.unpack("<I", bytearray[0:4])[0]

def bytes_to_shortint(bytearray):
    """Converts 2 bytes to a short integer"""
    return struct.unpack('H', bytearray)

def bytes_to_float(bytearray):
    """Converts 2 bytes to a short integer"""
    return struct.unpack('f', bytearray[0:4])


def read_bgra_color(bytearray):
    """reads 4 bytes into a BGRA color, and then converts to RGBA"""
    color = []
    for j in range(4):
        color.append(ord(bytearray[j:j + 1]))
    tempblue = color[0]
    color[0] = color[2]
    color[2] = tempblue
    return color

def isPowerOf2(number):
    """Checks if a number is a power of 2"""
    num1 = ((number & (number - 1)) == 0)
    return num1

previousMasks = {}

def calc_bitmasks_ARGB_color(bdR, bdG, bdB, bdA):
    key = str(bdA) + str(bdR) + str(bdG) + str(bdB)
    if key in previousMasks:
        masks = previousMasks[key]
        return masks
    
    redMask = 0
    greenMask = 0
    blueMask = 0
    alphaMask = 0

    if bdA > 0:
        for i in range(bdA):
            alphaMask = (alphaMask << 1) + 1
        alphaMask = alphaMask << (bdR + bdG + bdB)

    for i in range(bdR):
        redMask = (redMask << 1) + 1
    redMask = redMask << (bdG + bdB)

    greenMask = 0
    for i in range(bdG):
        greenMask = (greenMask << 1) + 1
    greenMask = greenMask << (bdB)

    blueMask = 0
    for i in range(bdB):
        blueMask = (blueMask << 1) + 1

    masks = [redMask, greenMask, blueMask, alphaMask]
    previousMasks[key] = masks
    return masks

def read_bitmask_ARGB_color(bytearray, bdR, bdG, bdB, bdA):
    """Reads an ARGB color with custom bit depths for each channel, returns in RGBA format"""
    colorVal = bytes_to_shortint(bytearray)[0]
    masks = calc_bitmasks_ARGB_color(bdR, bdG, bdB, bdA)
    redMask = masks[0]
    greenMask = masks[1]
    blueMask = masks[2]
    alphaMask = masks[3]

    alphaColor = 255  
    if bdA > 0:
        alphaColor = alphaMask & colorVal
        alphaColor = alphaColor >> (bdR + bdG + bdB)
        alphaMaxValue = 2 ** bdA
        #convert to full 255 range of color
        alphaColor = int((float(alphaColor) / float(alphaMaxValue)) * 255)

    redColor = redMask & colorVal
    redColor = redColor >> (bdG + bdB)
    redMaxValue = 2 ** bdR
    #convert to full 255 range of color
    redColor = int((float(redColor) / float(redMaxValue)) * 255)

    greenColor = greenMask & colorVal
    greenColor = greenColor >> (bdB)
    greenMaxValue = 2 ** bdG
    #convert to full 255 range of color
    greenColor = int((float(greenColor) / float(greenMaxValue)) * 255)

    blueColor = blueMask & colorVal
    blueMaxValue = 2 ** bdB
    #convert to full 255 range of color
    blueColor = int((float(blueColor) / float(blueMaxValue)) * 255)

    return [redColor, greenColor, blueColor, alphaColor]

def read_uint_array(bytearray, numelements):
    tempArray = []
    for i in range(numelements):
        temp = bytes_to_uint(bytearray[i*4])
        tempArray.append(temp)
    return tempArray

class MetaInfo(object):
    """Lazy wrapper to allow quick serialization of meta data"""

    def __init__(self):
        pass

    def setFilename(self, filename):
        self.filename = filename

    def add_info(self, key, info):
        self.__setattr__(key, info)

    def writeJSON(self, filename):
        fp = open(filename, "w")
        json.dump(self, fp, cls=CustomJSONEncoder, indent=4)
        fp.close()


class CustomJSONEncoder(json.JSONEncoder):
    """A quick and  dirty custom JSON encoder that allows serialization of custom objects"""
    #https://code.tutsplus.com/tutorials/serialization-and-deserialization-of-python-objects-part-1--cms-26183
    def default(self, o):
        return  o.__dict__
