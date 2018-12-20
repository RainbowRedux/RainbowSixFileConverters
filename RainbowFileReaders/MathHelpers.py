import math

def normalize_color(color):
    """ take an iterable object with values 0-255, and convert to 0.0-1.0 range
    returns tuple"""
    normColor = []
    for el in color:
        normColor.append(el / 255)
    return tuple(normColor)

def unnormalize_color(color):
    """ take an iterable object with values 0.0-1.0, and convert to 0-255 range
    returns tuple"""
    normColor = []
    for el in color:
        normColor.append(int(el * 255))
    return tuple(normColor)

def pad_color(color):
    """ take an iterable object, and add 1.0 elements until length is 4.
    returns tuple"""
    paddedColor = []
    for el in color:
        paddedColor.append(el)

    while len(paddedColor) < 4:
        paddedColor.append(1.0)
    return tuple(paddedColor)

def sanitize_float(inFloat):
    """converts float to string, with maximum of 8 decimal places, avoiding e-notation"""
    return "{0:.8f}".format(inFloat)

def is_vector_normal(normal):
    """Takes an iterable, calculates vector length, and then returns True if it is aproximately 1.0"""
    normalSquaredSum = 0
    for i in normal:
        normalSquaredSum += i * i
    normalSumSqrt = math.sqrt(normalSquaredSum)
    if normalSumSqrt > 0.9999 and normalSumSqrt < 1.0001:
        return True
    return False