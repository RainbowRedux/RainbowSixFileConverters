"""Contains data structures specific to Rogue Spear maps"""

import logging

from typing import List, Tuple, Dict

from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, BinaryFileReader, SizedCString
from FileUtilities.LoggingUtils import log_pprint
from RainbowFileReaders import R6Constants
from RainbowFileReaders.MathHelpers import IntIterable, pad_color
from RainbowFileReaders.RenderableArray import RenderableArray
from RainbowFileReaders.R6Constants import RSEGeometryFlags

log = logging.getLogger(__name__)

class RSMAPGeometryObject(BinaryFileDataStructure):
    """Geometry Object used in Rogue Spear maps"""
    def __init__(self):
        super(RSMAPGeometryObject, self).__init__()
        self.size: int = 0
        self.id: int = 0
        self.version_string: SizedCString = SizedCString()
        self.versionNumber: int = 0
        self.name_string: SizedCString = SizedCString()
        self.geometryData: RSMAPGeometryData = RSMAPGeometryData()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.size = filereader.read_uint32()
        self.id = filereader.read_uint32()

        self.version_string = SizedCString(filereader)
        self.versionNumber = filereader.read_uint32()

        self.name_string = SizedCString(filereader)

        self.geometryData = RSMAPGeometryData()
        self.geometryData.read(filereader)

class RSMAPFaceGroup(BinaryFileDataStructure):
    """Data structure defining a group of face definitions and some associated data"""
    def __init__(self):
        super(RSMAPFaceGroup, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.materialIndex: int = filereader.read_uint32()

        self.faceCount: int = filereader.read_uint32()

        self.faceNormals: List[List[float]] = []
        self.faceDistancesFromOrigin: List[float] = []

        for _ in range(self.faceCount):
            self.faceNormals.append(filereader.read_vec_f(3))
            self.faceDistancesFromOrigin.append(filereader.read_float())

        self.faceVertexIndices: List[List[int]] = []
        for _ in range(self.faceCount):
            self.faceVertexIndices.append(filereader.read_vec_uint16(3))

        self.faceVertexParamIndices: List[List[int]] = []
        for _ in range(self.faceCount):
            self.faceVertexParamIndices.append(filereader.read_vec_uint16(3))

        self.vertexParams: RSMAPVertexParameterCollection = RSMAPVertexParameterCollection()
        self.vertexParams.read(filereader)

class RSMAPGeometryData(BinaryFileDataStructure):
    """Datastructure within RSMAPGeometryObjects"""
    def __init__(self):
        super(RSMAPGeometryData, self).__init__()
        self.size: int = 0
        self.id: int = 0
        self.version_string: SizedCString = SizedCString()
        self.versionNumber: int = 0
        self.name_string: SizedCString = SizedCString()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.read_header_info(filereader)

        self.read_vertices(filereader)

        self.read_face_groups(filereader)

        self.collisionInformation = RSMAPCollisionInformation()
        self.collisionInformation.read(filereader)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.size = filereader.read_uint32()
        self.id = filereader.read_uint32()

        self.version_string = SizedCString(filereader)
        self.versionNumber = filereader.read_uint32()

        self.name_string = SizedCString(filereader)

    def generate_renderable_array_for_facegroup(self, facegroup: RSMAPFaceGroup):
        """ Generates a RenderableArray object from the internal data structure """
        renderable = RenderableArray()
        renderable.materialIndex = facegroup.materialIndex

        attribList: List[Tuple[int, int]] = []
        triangleIndices: List[IntIterable] = []

        for i in range(facegroup.faceCount):
            # Pack triangle indices into sub arrays per face for consistency with RenderableArray format
            currentTriangleIndices: List[int] = []

            currentVertIndices = facegroup.faceVertexIndices[i]
            currentVertParamIndices = facegroup.faceVertexParamIndices[i]
            numVerts = len(currentVertIndices)
            for j in range(numVerts):
                currentAttribIndices = (currentVertIndices[j], currentVertParamIndices[j])
                if currentAttribIndices not in attribList:
                    attribList.append(currentAttribIndices)
                currentTriangleIndices.append(attribList.index(currentAttribIndices))

            triangleIndices.append(currentTriangleIndices)

        #Create fresh lists for vertexColors and UVs
        renderable.vertexColors = []
        renderable.UVs = []
        for currentAttribSet in attribList:
            # Make sure to copy any arrays so any transforms don't get interferred with in other renderables
            currentVertex: List[float] = self.vertices[currentAttribSet[0]]
            currentVertParamIdx = currentAttribSet[1]

            renderable.vertices.append(currentVertex.copy())
            renderable.normals.append(facegroup.vertexParams.normals[currentVertParamIdx].copy())
            renderable.UVs.append(facegroup.vertexParams.UVs[currentVertParamIdx].copy())

            # Convert color to RenderableArray standard format, RGBA 0.0-1.0 range
            importedColorCopy: List[float] = facegroup.vertexParams.colors[currentVertParamIdx].copy()
            # convert the color to 0.0-1.0 range, rather than 0-255
            #TODO: Verify this is no longer needed
            #importedColor = normalize_color(importedColorCopy)
            # pad with an alpha value so it's RGBA
            importedColor = pad_color(importedColorCopy)
            renderable.vertexColors.append(importedColor)
        # set the triangle indices
        renderable.triangleIndices = triangleIndices

        return renderable

    def read_vertices(self, filereader: BinaryFileReader):
        """Reads the list of vertices from the file"""
        self.vertexCount = filereader.read_uint32()
        self.vertices: List[List[float]] = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

    def read_face_groups(self, filereader: BinaryFileReader):
        """Reads the list of RSMAPFaceGroups from the file"""
        self.faceGroupCount = filereader.read_uint32()
        self.faceGroups: List[RSMAPFaceGroup] = []

        for _ in range(self.faceGroupCount):
            newFaceGroup = RSMAPFaceGroup()
            newFaceGroup.read(filereader)
            self.faceGroups.append(newFaceGroup)

class RSMAPVertexParameterCollection(BinaryFileDataStructure):
    """A collection of vertex parameters including UVs, normals and colors"""
    def __init__(self):
        super(RSMAPVertexParameterCollection, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.vertexParamCount: int = filereader.read_uint32()

        self.normals: List[List[float]] = []
        for _ in range(self.vertexParamCount):
            self.normals.append(filereader.read_vec_f(3))

        self.UVs: List[List[float]] = []
        for _ in range(self.vertexParamCount):
            self.UVs.append(filereader.read_vec_f(2))

        self.colors: List[List[float]] = []
        for _ in range(self.vertexParamCount):
            self.colors.append(filereader.read_vec_f(4))

class RSMAPCollisionInformation(BinaryFileDataStructure):
    """Stores more geometry which is specifically used for collision, pathing, and map planning etc"""
    def __init__(self):
        super(RSMAPCollisionInformation, self).__init__()

        # These vertices and normals don't line up with the vertex and normal indices.
        # I suspect these are used for bounding boxes / simplified geometry
        self.vertexCount: int = 0
        self.vertices: List[List[float]] = []
        self.normalCount: int = 0
        self.normals: List[List[float]] = []
        self.faceDistancesFromOrigin: List[float] = []

        # Face definitions
        self.faceCount: int = 0
        self.faces: List[RSMAPCollisionFaceInformation] = []

        # collision mesh definitions, collection of faces and geometry flags
        self.collisionMeshDefinitionsCount: int = 0
        self.collisionMeshDefinitions: List[RSMAPCollisionMesh] = []

    def generate_renderable_array_for_collisionmesh(self, collisionMesh, geometryData):
        """Generates RenderableArray objects for each collision mesh defined"""
        attribList = []
        triangleIndices = []

        for faceIdx in collisionMesh.faceIndices:
            currentFace = self.faces[faceIdx]
            currentVertIndices = currentFace.vertexIndices
            currentVertNormIndices = currentFace.normalIndices

            currentTriangleIndices = []

            numVerts = len(currentVertIndices)
            for j in range(numVerts):
                currentAttribs = (currentVertIndices[j], currentVertNormIndices[j])
                if currentAttribs in attribList:
                    currentTriangleIndices.append(attribList.index(currentAttribs))
                else:
                    attribList.append(currentAttribs)
                    currentTriangleIndices.append(attribList.index(currentAttribs))

            triangleIndices.append(currentTriangleIndices)

        currentRenderable = RenderableArray()
        currentRenderable.materialIndex = R6Constants.UINT_MAX

        for currentAttribSet in attribList:
            currentVertex = None
            try:
                currentVertex = geometryData.vertices[currentAttribSet[0]]
                #currentNormal = geometryData.normals[currentAttribSet[1]]
            except IndexError:
                log.error("Error in mesh. Vertex index out of range")
                log.error(str(currentAttribSet[0]))
                log_pprint(collisionMesh.geometryFlags, logging.ERROR)
                exit(1)

            currentRenderable.vertices.append(currentVertex.copy())
            #currentRenderable.normals.append(currentNormal.copy())

        #Explicitly state that there are no values for these attributes
        currentRenderable.UVs = None
        currentRenderable.vertexColors = None
        currentRenderable.triangleIndices = triangleIndices

        return currentRenderable

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.vertexCount = filereader.read_uint32()

        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.normalCount = filereader.read_uint32()

        self.normals = []
        self.faceDistancesFromOrigin = []

        for _ in range(self.normalCount):
            self.normals.append(filereader.read_vec_f(3))
            self.faceDistancesFromOrigin.append(filereader.read_float())

        self.faceCount = filereader.read_uint32()

        self.faces = []
        for _ in range(self.faceCount):
            faceObject = RSMAPCollisionFaceInformation()
            faceObject.read(filereader)
            self.faces.append(faceObject)

        self.collisionMeshDefinitionsCount = filereader.read_uint32()
        self.collisionMeshDefinitions = []
        for _ in range(self.collisionMeshDefinitionsCount):
            dataObject = RSMAPCollisionMesh()
            dataObject.read(filereader)
            self.collisionMeshDefinitions.append(dataObject)

class RSMAPCollisionFaceInformation(BinaryFileDataStructure):
    """Defines a face for a mesh, specifically collision related"""
    def __init__(self):
        super(RSMAPCollisionFaceInformation, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.vertexIndices: List[int] = filereader.read_vec_uint16(3)

        self.unknown1: int = filereader.read_uint16()

        self.normalIndices: List[int] = filereader.read_vec_uint16(3)

        self.unknown2: int = filereader.read_uint16()


class RSMAPCollisionMesh(BinaryFileDataStructure):
    """Defines a mesh used in collision. Specifies what faces are used and what GeometryFlags are applied"""
    def __init__(self):
        super(RSMAPCollisionMesh, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.name_string: SizedCString = SizedCString(filereader)

        self.geometryFlags: int = filereader.read_uint32() #??
        self.geometryFlagsEvaluated: Dict[str, bool] = RSEGeometryFlags.EvaluateFlags(self.geometryFlags)

        self.faceCount: int = filereader.read_uint32()
        self.faceIndices: List[int] = filereader.read_vec_uint16(self.faceCount)

class RSMAPRoomDefinition(BinaryFileDataStructure):
    """Defines a Room as used in Rainbow Six. Contains information such as levels"""
    def __init__(self):
        super(RSMAPRoomDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.id: int = filereader.read_uint32()
        self.version_string: SizedCString = SizedCString(filereader)
        self.versionNumber: int = filereader.read_uint32()

        self.name_string: SizedCString = SizedCString(filereader)

        self.unknown1: int = filereader.read_bytes(1)[0] #A
        self.unknown2: int = filereader.read_bytes(1)[0] #B
        self.unknown3: int = filereader.read_bytes(1)[0] #C
        if self.unknown1 == 0:
            self.unknown4: int = filereader.read_bytes(1)[0] #D

        if self.unknown3 == 1:
            self.unknown5: List[float] = filereader.read_vec_f(6)

        if self.unknown1 == 0 and self.unknown4 == 1:
            self.unknown6: List[float] = filereader.read_vec_f(6)

        self.shermanLevelCount: int = filereader.read_uint32()
        self.shermanLevels: List[RSMAPShermanLevelDefinition] = []
        for _ in range(self.shermanLevelCount):
            newObject = RSMAPShermanLevelDefinition()
            newObject.read(filereader)
            self.shermanLevels.append(newObject)


        self.unknown4Count: int = filereader.read_uint32()

        self.unknown7: float = filereader.read_float()
        self.unknown8: List[List[float]] = []
        for _ in range(self.unknown4Count):
            newUnknown8 = filereader.read_vec_f(2)
            self.unknown8.append(newUnknown8)


class RSMAPShermanLevelDefinition(BinaryFileDataStructure):
    """Contains a level definition as used in Rogue Spear"""
    def __init__(self):
        super(RSMAPShermanLevelDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.name_string: SizedCString = SizedCString(filereader)
        self.transformCount: int = filereader.read_uint32() # ACount
        self.transforms: List[RSMAPShermanLevelTransformInformation] = []
        for _ in range(self.transformCount):
            transformObj = RSMAPShermanLevelTransformInformation()
            transformObj.read(filereader)
            self.transforms.append(transformObj)

        self.unknown3Count: int = filereader.read_uint32()
        self.unknown3: List[float] = filereader.read_vec_f(self.unknown3Count)

        self.unknown4: int = filereader.read_bytes(1)[0]

class RSMAPShermanLevelTransformInformation(BinaryFileDataStructure):
    """Defines a transform used for a level? Still decoding"""
    def __init__(self):
        super(RSMAPShermanLevelTransformInformation, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        #3x3 matrix = 9 elements
        self.transformMatrix: List[float] = filereader.read_vec_f(9)
        self.position: List[float] = filereader.read_vec_f(3)
        self.unknown2: List[float] = filereader.read_vec_f(6) #size?

class RSMAPShermanLevelTransitionList(BinaryFileDataStructure):
    """This is related to the portal system and traversal between floors, but exact details and usage is still TBD"""
    def __init__(self):
        super(RSMAPShermanLevelTransitionList, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_transition_objects(filereader)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.transitionListSize: int = filereader.read_uint32() #L, moved here to match other header structures
        self.id: int = filereader.read_uint32()
        self.section_string: SizedCString = SizedCString(filereader)

    def read_transition_objects(self, filereader: BinaryFileReader):
        """Reads the transition objects into a list"""
        self.transitionCount: int = filereader.read_uint32()
        self.transitions: List[RSMAPShermanLevelTransitionDefinition] = []
        for _ in range(self.transitionCount):
            transition = RSMAPShermanLevelTransitionDefinition()
            transition.read(filereader)
            self.transitions.append(transition)

class RSMAPShermanLevelTransitionDefinition(BinaryFileDataStructure):
    """This is related to the portal system and traversal between floors, but exact details and usage is still TBD"""
    def __init__(self):
        super(RSMAPShermanLevelTransitionDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.name_string: SizedCString = SizedCString(filereader)
        log.debug(self.name_string.string)

        self.coords: List[float] = filereader.read_vec_f(6)
