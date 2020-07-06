"""
Provides some utility functions for converting colors
"""
import functools

from typing import List, Tuple, Dict
from math import floor

#Provides a lookup table for every color in each color format.
COLOR_LOOKUPS: Dict[str, List[int]] = {}

#Stores a lookup list for every bitdepth
BITDEPTH_VALUE_LOOKUPS: Dict[int, List[int]] = {}

class ColorFormats(object):
    """Used to store constants representing the different color formats"""
    CF_ARGB_4444 = "ARGB4444"
    CF_ARGB_0565 = "ARGB0565"
    CF_UNKNOWN = "UNKNOWN"

def get_color_format(bdR, bdG, bdB, bdA):
    """ Determines the color format, which can be used for color lookup tables """
    if bdR == 4 and bdG == 4 and bdB == 4 and bdA == 4:
        return ColorFormats.CF_ARGB_4444

    if bdR == 5 and bdG == 6 and bdB == 5 and bdA == 0:
        return ColorFormats.CF_ARGB_0565

    return ColorFormats.CF_UNKNOWN

def get_color_lookup_table(color_format):
    """Returns the lookup table for a given color format"""
    return COLOR_LOOKUPS[color_format]

def calculate_bitdepth_lookup(bitdepth):
    """Calculates a lookup table mapping a quantized value to an appropriate 0-255 value for a given bitdepth"""
    bdMaxValue = 2 ** bitdepth - 1
    colors = []
    for colorVal in range(bdMaxValue + 1):
        #convert to full 255 range of color
        colorFlt = float(colorVal) / float(bdMaxValue) * 255
        finalColor = int(floor(colorFlt))
        colors.append(finalColor)
    BITDEPTH_VALUE_LOOKUPS[bitdepth] = colors

def build_bitdepth_lookups():
    """Build a color lookup table for each quantized value in a given bitdepth"""
    calculate_bitdepth_lookup(4)
    calculate_bitdepth_lookup(5)
    calculate_bitdepth_lookup(6)

def build_4444_color_lookup():
    """Build the lookup table for the ARGB_4444 color format"""
    bdR = 4
    bdG = 4
    bdB = 4
    alphaColorOffset = bdR + bdG + bdB
    redColorOffset = bdG + bdB
    greenColorOffset = bdB
    val_lookup_4 = BITDEPTH_VALUE_LOOKUPS[4]

    conversion_table = [None] * 65536

    for a_short, a_value in enumerate(val_lookup_4):
        a_offset = a_short << alphaColorOffset
        for r_short, r_value in enumerate(val_lookup_4):
            r_offset = r_short << redColorOffset
            ar_offset = a_offset | r_offset
            for g_short, g_value in enumerate(val_lookup_4):
                g_offset = g_short << greenColorOffset
                arg_offset = ar_offset | g_offset
                for b_short, b_value in enumerate(val_lookup_4):
                    final_color_code = arg_offset | b_short
                    final_color_tuple = (r_value, g_value, b_value, a_value)
                    conversion_table[final_color_code] = final_color_tuple

    return conversion_table

def build_0565_color_lookup():
    """Build the lookup table for the ARGB_0565 color format"""
    bdG = 6
    bdB = 5
    redColorOffset = bdG + bdB
    greenColorOffset = bdB
    val_lookup_5 = BITDEPTH_VALUE_LOOKUPS[5]
    val_lookup_6 = BITDEPTH_VALUE_LOOKUPS[6]

    conversion_table = [None] * 65536

    for r_short, r_value in enumerate(val_lookup_5):
        r_offset = r_short << redColorOffset
        for g_short, g_value in enumerate(val_lookup_6):
            g_offset = g_short << greenColorOffset
            rg_offset = r_offset | g_offset
            for b_short, b_value in enumerate(val_lookup_5):
                final_color_code = rg_offset | b_short
                final_color_tuple = (r_value, g_value, b_value, 255)
                conversion_table[final_color_code] = final_color_tuple

    return conversion_table


def build_color_lookups():
    """Builds the lookup tables for each color format"""
    build_bitdepth_lookups()
    COLOR_LOOKUPS[ColorFormats.CF_ARGB_4444] = build_4444_color_lookup()
    COLOR_LOOKUPS[ColorFormats.CF_ARGB_0565] = build_0565_color_lookup()

@functools.lru_cache(maxsize=8)
def calc_bitmasks_ARGB_color(bdR: int, bdG: int, bdB: int, bdA: int):
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
def read_bitmask_ARGB_color(colorVal: int, bdR: int, bdG: int, bdB: int, bdA: int) -> Tuple[int, int, int, int]:
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
        alphaColorFlt = float(alphaColor) / float(alphaMaxValue) * 255
        alphaColor = int(floor(alphaColorFlt))

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

    return (redColor, greenColor, blueColor, alphaColor)

if len(COLOR_LOOKUPS.keys()) == 0:
    build_color_lookups()
