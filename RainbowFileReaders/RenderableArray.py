"""Contains data structures and related functions for renderable geometry"""

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

class RenderableArray(object):
    """Stores geometry information in a way that's closer to how renderers work, can easily be adapted to each engine from this method.
    This structure should be generated by all format readers.
    All parameter arrays should be equal in length, with the exception of triangle indices
    Triangle indices refer to the same element index in every array. You cannot specify vertex I, normal J, etc"""
    def __init__(self):
        super(RenderableArray, self).__init__()
        self.vertices = []
        self.vertexColors = []
        self.normals = []
        self.UVs = []
        self.materialIndex = None
        self.triangleIndices = []

    def calculate_AABB(self):
        """Calculates and returns an Axis Aligned Bounding Box structure"""
        AABB = AxisAlignedBoundingBox()
        for vertex in self.vertices:
            AABB.add_point(vertex)
        return AABB

    def scale(self, scale):
        """Performs a scaling operation on each vertex"""
        for vertex in self.vertices:
            vertex[0] = vertex[0] * scale[0]
            vertex[1] = vertex[1] * scale[1]
            vertex[2] = vertex[2] * scale[2]

    def translate(self, translation):
        """Translates all vertices by this amount"""
        for vertex in self.vertices:
            vertex[0] = vertex[0] + translation[0]
            vertex[1] = vertex[1] + translation[1]
            vertex[2] = vertex[2] + translation[2]

    def merge(self, otherRenderable):
        """Merges in geometry from another renderable into this one."""
        if otherRenderable is None:
            return

        indexOffset = len(self.vertices)

        self.vertices.extend(otherRenderable.vertices)
        self.vertexColors.extend(otherRenderable.vertexColors)
        self.normals.extend(otherRenderable.normals)
        self.UVs.extend(otherRenderable.UVs)

        for triangle in otherRenderable.triangleIndices:
            newTri = []
            for triIdx in triangle:
                newIdx = triIdx + indexOffset
                newTri.append(newIdx)
            self.triangleIndices.append(newTri)