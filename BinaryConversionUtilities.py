import struct
import json

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
    for j in xrange(4):
        color.append(ord(bytearray[j:j + 1]))
    tempblue = color[0]
    color[0] = color[2]
    color[2] = tempblue
    return color

previousMasks = {}

def calc_bitmasks_RGBA_color(bdR, bdG, bdB, bdA):
    key = str(bdR) + str(bdG) + str(bdB) + str(bdA)
    if key in previousMasks:
        masks = previousMasks[key]
        return masks
    
    redMask = 0
    greenMask = 0
    blueMask = 0
    alphaMask = 0

    for i in xrange(bdR):
        redMask = (redMask << 1) + 1
    redMask = redMask << (bdG + bdB + bdA)

    greenMask = 0
    for i in xrange(bdG):
        greenMask = (greenMask << 1) + 1
    greenMask = greenMask << (bdB + bdA)

    blueMask = 0
    for i in xrange(bdB):
        blueMask = (blueMask << 1) + 1
    blueMask = blueMask << (bdA)

    if bdA > 0:
        alphaMask = 0
        for i in xrange(bdA):
            alphaMask = (alphaMask << 1) + 1

    masks = [redMask, greenMask, blueMask, alphaMask]
    previousMasks[key] = masks
    return masks

def read_bitmask_RGBA_color(bytearray, bdR, bdG, bdB, bdA):
    """Reads an RGBA color with custom bit depths for each channel"""
    colorVal = bytes_to_shortint(bytearray)[0]
    masks = calc_bitmasks_RGBA_color(bdR, bdG, bdB, bdA)
    redMask = masks[0]
    greenMask = masks[1]
    blueMask = masks[2]
    alphaMask = masks[3]

    redColor = redMask & colorVal
    redColor = redColor >> (bdG + bdB + bdA)
    redMaxValue = 2 ** bdR
    #convert to full 255 range of color
    redColor = int((float(redColor) / float(redMaxValue)) * 255)

    greenColor = greenMask & colorVal
    greenColor = greenColor >> (bdB + bdA)
    greenMaxValue = 2 ** bdG
    #convert to full 255 range of color
    greenColor = int((float(greenColor) / float(greenMaxValue)) * 255)

    blueColor = blueMask & colorVal
    blueColor = blueColor >> (bdA)
    blueMaxValue = 2 ** bdB
    #convert to full 255 range of color
    blueColor = int((float(blueColor) / float(blueMaxValue)) * 255)

    alphaColor = 255
    if bdA > 0:
        alphaColor = alphaMask & colorVal
        alphaMaxValue = 2 ** bdA
        #convert to full 255 range of color
        alphaColor = int((float(alphaColor) / float(alphaMaxValue)) * 255)

    return [redColor, greenColor, blueColor, alphaColor]

def read_uint_array(bytearray, numelements):
    tempArray = []
    for i in xrange(numelements):
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
