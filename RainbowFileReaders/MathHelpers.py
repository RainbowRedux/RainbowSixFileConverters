""" This module contains a number of useful math related functions that are used throughout this project """
import math

class AxisAlignedBoundingBox(object):
    """Contains data for an Axis Aligned Bounding Box"""
    def __init__(self):
        super(AxisAlignedBoundingBox, self).__init__()
        self.bInitialized = False
        self.minX = 0
        self.minY = 0
        self.minZ = 0

        self.maxX = 0
        self.maxY = 0
        self.maxZ = 0

    def add_point(self, vertex):
        """Adds a point to be considered for this AABB. This expands the AABB dimensions immediately."""
        #If not initialized, set the limits to match this point
        if self.bInitialized is False:
            self.bInitialized = True
            self.minX = vertex[0]
            self.maxX = vertex[0]
            self.minY = vertex[1]
            self.maxY = vertex[1]
            self.minZ = vertex[2]
            self.maxZ = vertex[2]
            return

        if self.minX > vertex[0]:
            self.minX = vertex[0]
        if self.maxX < vertex[0]:
            self.maxX = vertex[0]

        if self.minY > vertex[1]:
            self.minY = vertex[1]
        if self.maxY < vertex[1]:
            self.maxY = vertex[1]

        if self.minZ > vertex[2]:
            self.minZ = vertex[2]
        if self.maxZ < vertex[2]:
            self.maxZ = vertex[2]

    def get_center_position(self):
        """Returns a point which is exactly in the center of this AABB. Useful for working out offsets, pivots etc"""
        X_size = self.maxX - self.minX
        X = self.minX + (X_size / 2)

        Y_size = self.maxY - self.minY
        Y = self.minY + (Y_size / 2)

        Z_size = self.maxZ - self.minZ
        Z = self.minZ + (Z_size / 2)

        position = [X, Y, Z]
        return position

    def merge(self, other):
        """Creates a new AABB which has a size that encompasses both self and other"""
        if self.bInitialized is False and other.bInitialized is False:
            return self

        if self.bInitialized is False:
            return other

        newAABB = AxisAlignedBoundingBox()
        newAABB.bInitialized = True

        if self.minX > other.minX:
            newAABB.minX = other.minX
        else:
            newAABB.minX = self.minX

        if self.minY > other.minY:
            newAABB.minY = other.minY
        else:
            newAABB.minY = self.minY

        if self.minZ > other.minZ:
            newAABB.minZ = other.minZ
        else:
            newAABB.minZ = self.minZ

        if self.maxX < other.maxX:
            newAABB.maxX = other.maxX
        else:
            newAABB.maxX = self.maxX

        if self.maxY < other.maxY:
            newAABB.maxY = other.maxY
        else:
            newAABB.maxY = self.maxY

        if self.maxZ < other.maxZ:
            newAABB.maxZ = other.maxZ
        else:
            newAABB.maxZ = self.maxZ

        return newAABB

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
    vector_length = Vector.get_length(normal)
    if vector_length > 0.9999 and vector_length < 1.0001:
        return True
    return False

def calc_vector_length(vector):
    length = Vector.get_length(vector)
    return length

class Vector(object):
    @staticmethod
    def get_length(vector_array):
        """Calculates a vector length. vector_array is an iterable"""
        squaredSum = 0
        for i in vector_array:
            squaredSum += i * i
        length = math.sqrt(squaredSum)
        return length

    @staticmethod
    def get_normal(vector_array):
        """Calculates a vector normal. vector_array is an iterable"""
        length = Vector.get_length(vector_array)
        normal = Vector.divide_scalar(vector_array, length)
        return normal

    @staticmethod
    def add_scalar(vecA, scalar):
        """Adds a scalar to a vector.
        Element wise operation"""
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] + scalar)
        return result

    @staticmethod
    def subtract_scalar(vecA, scalar):
        """Subtracts a scalar from a vector.
        Element wise operation"""
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] - scalar)
        return result

    @staticmethod
    def multiply_scalar(vecA, scalar):
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] * scalar)
        return result

    @staticmethod
    def divide_scalar(vecA, scalar):
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] / scalar)
        return result

    @staticmethod
    def add_vector(vecA, vecB):
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] + vecB[i])
        return result

    @staticmethod
    def subtract_vector(vecA, vecB):
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] - vecB[i])
        return result

    @staticmethod
    def multiply_vector(vecA, vecB):
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] * vecB[i])
        return result

    @staticmethod
    def divide_vector(vecA, vecB):
        result = []
        for i in range(len(vecA)):
            result.append(vecA[i] / vecB[i])
        return result

    @staticmethod
    def dot(vecA, vecB):
        """Calculates the dot product of 2 vectors. This function normalizes vectors first to ensure consistent results"""
        vecANorm = Vector.get_normal(vecA)
        vecBNorm = Vector.get_normal(vecB)
        multipliedVec = Vector.multiply_vector(vecANorm, vecBNorm)
        sum
        resultSum = 0
        for el in multipliedVec:
            resultSum += el
        return resultSum

    @staticmethod
    def get_angle(vecA, vecB):
        """Returns the angle between 2 vectors, expressed in radians"""
        dotproduct = Vector.dot(vecA, vecB)
        theta = math.acos(dotproduct)
        return theta

    @staticmethod
    def cross(vecA, vecB):
        """Returns the cross product between 2 vectors. Both vectors should be lists that are exactly 3 elements long"""
        X = vecA[1] * vecB[2] - vecA[2] * vecB[1]
        Y = vecA[2] * vecB[0] - vecA[0] * vecB[2]
        Z = vecA[0] * vecB[1] - vecA[1] * vecB[0]
        cross = [X, Y, Z]
        return cross
        