"""
This module defines the fileformat and data structures specific to MAP files used in Rainbow Six and Rogue Spear
"""
from __future__ import annotations
import logging
from typing import List, Union, Tuple, Any, Dict, Optional
from datetime import datetime

from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader, SizedCString, BinaryFileReader
from FileUtilities.LoggingUtils import log_pprint
from RainbowFileReaders import R6Settings, R6Constants
from RainbowFileReaders.R6Constants import RSEGameVersions, RSEGeometryFlags
from RainbowFileReaders.RSEGeometryDataStructures import RSEGeometryListHeader, R6GeometryObject, R6VertexParameterCollection, R6FaceDefinition
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader
from RainbowFileReaders.CXPMaterialPropertiesReader import load_relevant_cxps
from RainbowFileReaders.RSDMPLightReader import RSDMPLightFile
from RainbowFileReaders.MathHelpers import normalize_color, pad_color, Vector, AxisAlignedBoundingBox
from RainbowFileReaders.RenderableArray import RenderableArray

log = logging.getLogger(__name__)

class MAPLevelFile(FileFormatReader):
    """Class to read full MAP files"""
    def __init__(self):
        super(MAPLevelFile, self).__init__()
        self.header: MAPHeader = None
        self.materialListHeader: RSEMaterialListHeader  = None
        self.materials: List[RSEMaterialDefinition] = []
        self.geometryListHeader: RSEGeometryListHeader = None
        self.geometryObjects: List[Union[R6GeometryObject, RSMAPGeometryObject]] = []
        self.portalList: RSEMAPPortalList = []
        self.lightList: RSEMAPPortalList = []
        self.objectList: RSEMAPObjectList = []
        self.dmpLights: RSDMPLightFile = None

        self.footer: RSEMAPFooterDefinition = None
        #Game version is not stored in file, and has to be determined by analysing the structure of stored materials. Stored here for easy use
        self.gameVersion: str = RSEGameVersions.UNKNOWN

    def read_data(self):
        super().read_data()

        fileReader = self._filereader

        self.header = MAPHeader()
        self.header.read(fileReader)
        if self.verboseOutput:
            self.header.print_structure_info()

        self.materialListHeader = RSEMaterialListHeader()
        self.materialListHeader.read(fileReader)
        if self.verboseOutput:
            self.materialListHeader.print_structure_info()

        _, gameDataPath, modPath = R6Settings.determine_data_paths_for_file(self.filepath)
        CXPDefinitions = load_relevant_cxps(gameDataPath, modPath)

        self.materials = []
        for _ in range(self.materialListHeader.numMaterials):
            newMaterial = RSEMaterialDefinition()
            newMaterial.read(fileReader)
            newMaterial.add_CXP_information(CXPDefinitions)
            self.materials.append(newMaterial)
            if self.verboseOutput:
                pass

        if self.materials:
            self.gameVersion = self.materials[0].get_material_game_version()

        self.geometryListHeader = RSEGeometryListHeader()
        self.geometryListHeader.read(fileReader)
        if self.verboseOutput:
            self.geometryListHeader.print_structure_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            if self.gameVersion == RSEGameVersions.ROGUE_SPEAR:
                newObj = RSMAPGeometryObject()
                newObj.read(fileReader)
                self.geometryObjects.append(newObj)
                if self.verboseOutput:
                    pass
            else:
                newObj = R6GeometryObject()
                newObj.read(fileReader)
                self.geometryObjects.append(newObj)
                if self.verboseOutput:
                    pass

        self.portalList = RSEMAPPortalList()
        self.portalList.read(fileReader)

        self.lightList = R6MAPLightList()
        self.lightList.read(fileReader)

        self.objectList = RSEMAPObjectList()
        self.objectList.read(fileReader)

        self.roomList = RSEMAPRoomList()
        self.roomList.read_room_list(fileReader, self.gameVersion)

        if self.gameVersion == RSEGameVersions.ROGUE_SPEAR:
            self.transitionList = RSMAPShermanLevelTransitionList()
            self.transitionList.read(fileReader)

        self.planningLevelList = RSEMAPPlanningLevelList()
        self.planningLevelList.read_planning_level_list(fileReader, self.gameVersion)

        self.footer = RSEMAPFooterDefinition()
        self.footer.read(fileReader)

        #read in DMP file data
        if self.gameVersion == RSEGameVersions.ROGUE_SPEAR:
            if self.filepath.lower().endswith(".map"):
                lightFileName = self.filepath[:-4] + ".dmp"
                lightFile = RSDMPLightFile()
                lightFile.read_file(lightFileName)
                self.dmpLights = lightFile


class MAPHeader(BinaryFileDataStructure):
    """Header data structure for MAP files"""
    def __init__(self):
        super(MAPHeader, self).__init__()
        self.time: datetime = datetime.now()
        self.timePOSIXRaw: int = 0

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.header_begin_message = SizedCString(filereader)
        self.timePOSIXRaw = filereader.read_uint32()
        #special case handling, some files have a zero timestamp recorded, which datetime.fromtimestamp() doesn't like
        if self.timePOSIXRaw == 0:
            self.time = datetime(1970,1,1)
        else:
            self.time = datetime.fromtimestamp(self.timePOSIXRaw)

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

        #PETODO: Work out what this tuple actually is
        attribList: List[Tuple[Any, Any]] = []
        triangleIndices = []

        for i in range(facegroup.faceCount):
            # Pack triangle indices into sub arrays per face for consistency with RenderableArray format
            currentTriangleIndices = []

            currentVertIndices = facegroup.faceVertexIndices[i]
            currentVertParamIndices = facegroup.faceVertexParamIndices[i]
            numVerts = len(currentVertIndices)
            for j in range(numVerts):
                currentAttribs = (currentVertIndices[j], currentVertParamIndices[j])
                if currentAttribs in attribList:
                    currentTriangleIndices.append(attribList.index(currentAttribs))
                else:
                    attribList.append(currentAttribs)
                    currentTriangleIndices.append(attribList.index(currentAttribs))

            triangleIndices.append(currentTriangleIndices)

        for currentAttribSet in attribList:
            # Make sure to copy any arrays so any transforms don't get interferred with in other renderables
            currentVertex = self.vertices[currentAttribSet[0]]
            currentVertParamIdx = currentAttribSet[1]


            renderable.vertices.append(currentVertex.copy())
            renderable.normals.append(facegroup.vertexParams.normals[currentVertParamIdx].copy())
            renderable.UVs.append(facegroup.vertexParams.UVs[currentVertParamIdx].copy())

            # Convert color to RenderableArray standard format, RGBA 0.0-1.0 range
            importedColor = facegroup.vertexParams.colors[currentVertParamIdx].copy()
            # convert the color to 0.0-1.0 range, rather than 0-255
            importedColor = normalize_color(importedColor)
            # pad with an alpha value so it's RGBA
            importedColor = pad_color(importedColor)
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

        self.faceVertexIndices = []
        for _ in range(self.faceCount):
            self.faceVertexIndices.append(filereader.read_vec_uint16(3))

        self.faceVertexParamIndices: List[List[int]] = []
        for _ in range(self.faceCount):
            self.faceVertexParamIndices.append(filereader.read_vec_uint16(3))

        self.vertexParams: RSMAPVertexParameterCollection = RSMAPVertexParameterCollection()
        self.vertexParams.read(filereader)


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

class RSEMAPPortalList(BinaryFileDataStructure):
    """Contains a list of RSEMAPPortals used for occlusion culling"""
    def __init__(self):
        super(RSEMAPPortalList, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_portals(filereader)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.portalListSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()

        self.section_string: SizedCString = SizedCString(filereader)

    def read_portals(self, filereader: BinaryFileReader):
        """reads all portals in list"""
        self.portalCount: int = filereader.read_uint32()
        self.portals: List[RSEMAPPortal] = []
        for _ in range(self.portalCount):
            newPortal = RSEMAPPortal()
            newPortal.read(filereader)
            self.portals.append(newPortal)

class RSEMAPPortal(BinaryFileDataStructure):
    """Defines a portal used for visibility determination/occlusion culling"""
    def __init__(self):
        super(RSEMAPPortal, self).__init__()

    def generate_renderable_array_object(self) -> RenderableArray:
        """Generates RenderableArray object for a portal"""
        # Hard coded triangle indices as file format only specifies 4 indices
        triangleIndices = [ [0,1,2],
                            [0,2,3] ]

        currentRenderable = RenderableArray()
        currentRenderable.materialIndex = R6Constants.UINT_MAX

        for vertex in self.vertices:
            currentRenderable.vertices.append(vertex.copy())

        #calculate the normal of the first triangle
        line1 = Vector.subtract_vector(self.vertices[0], self.vertices[1])
        line2 = Vector.subtract_vector(self.vertices[1], self.vertices[2])
        crossProductNormal = Vector.cross(line1,line2)

        #use the same normal for all vertices
        currentRenderable.normals = []
        for vertex in currentRenderable.vertices:
            currentRenderable.normals.append(crossProductNormal.copy())

        #Explicitly state that there are no values for these attributes
        currentRenderable.UVs = None
        currentRenderable.vertexColors = None
        currentRenderable.triangleIndices = triangleIndices

        return currentRenderable

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.portalSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()

        self.version_string: SizedCString = SizedCString(filereader)
        self.versionNumber: int = filereader.read_uint32()

        self.name_string: SizedCString = SizedCString(filereader)

        self.vertexCount: int = filereader.read_uint32()
        self.vertices: List[List[float]] = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.roomA: int = filereader.read_uint32()
        self.roomB: int = filereader.read_uint32()


class R6MAPLightList(BinaryFileDataStructure):
    """Contains a list of lights. Appears in both Rainbow Six and Rogue Spear maps, but is always empty in Rogue Spear"""
    def __init__(self):
        super(R6MAPLightList, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_lights(filereader)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.lightListSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()

        self.section_string: SizedCString = SizedCString(filereader)

    def read_lights(self, filereader: BinaryFileReader):
        """Reads all lights into list"""
        self.lightCount: int = filereader.read_uint32()

        self.lights: List[R6MAPLight] = []
        for _ in range(self.lightCount):
            newLight = R6MAPLight()
            newLight.read(filereader)
            self.lights.append(newLight)

class R6MAPLight(BinaryFileDataStructure):
    """A light definition for lights stored in Rainbow Six MAP files"""
    def __init__(self):
        super(R6MAPLight, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.lightSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()

        #Some maps store a version string, others don't, not quite sure why. Also makes unknown6 quite unclear as to whether they are separate fields or not
        self.name_string: SizedCString = SizedCString(filereader)
        if self.name_string.string == "Version":
            self.version_string: SizedCString = self.name_string
            self.versionNumber: int = filereader.read_uint32()

            self.name_string = SizedCString(filereader)
            self.unknown6: int = filereader.read_uint32()
        else:
            self.unknown7: bytes = filereader.read_bytes(3)

        #3x3 matrix = 9 elements
        self.transformMatrix: List[float] = filereader.read_vec_f(9)

        self.position: List[float] = filereader.read_vec_f(3)
        self.color: List[int] = filereader.read_vec_uint32(3)
        self.constantAttenuation: float = filereader.read_float()
        self.linearAttenuation: float = filereader.read_float()
        self.quadraticAttenuation: float = filereader.read_float()
        #maybe?
        self.falloff: float = filereader.read_float()
        self.energy: float = filereader.read_float()
        self.type: int = filereader.read_bytes(1)[0]

class RSEMAPObjectList(BinaryFileDataStructure):
    """A list of all dynamic objects in the map, including doors, breakable glass, etc"""
    def __init__(self):
        super(RSEMAPObjectList, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_objects(filereader)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.objectListSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()
        self.section_string: SizedCString = SizedCString(filereader)

    def read_objects(self, filereader: BinaryFileReader):
        """Reads all objects into a list"""
        self.objectCount: int = filereader.read_uint32()

        self.objects: List[RSEMAPObject] = []
        for _ in range(self.objectCount):
            newObject = RSEMAPObject()
            newObject.read(filereader)
            self.objects.append(newObject)

class RSEMAPObject(BinaryFileDataStructure):
    """Stores a dynamic object such as doors, breakable glass etc"""
    def __init__(self):
        super(RSEMAPObject, self).__init__()
        self.bytes: bytes = b''

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)
        #PETODO: Move these to R6 Constants?
        RS_OBJECT_VERSION = 5
        R6_OBJECT_VERSION = 1

        self.objectSize: int = filereader.read_uint32()
        self.objectType: int = filereader.read_uint32()
        self.version_string: SizedCString = SizedCString(filereader)
        self.versionNumber: int = filereader.read_uint32()
        self.name_string: SizedCString = SizedCString(filereader)

        if self.versionNumber >= RS_OBJECT_VERSION:
            self.bytes = filereader.read_bytes(self.objectSize)
        elif self.versionNumber == R6_OBJECT_VERSION:
            numberOfBytesToSkip = self.objectSize
            #skip 4 uints
            numberOfBytesToSkip = numberOfBytesToSkip - 4*4
            #skip the length of the 2 strings
            numberOfBytesToSkip = numberOfBytesToSkip - self.name_string.string_length
            numberOfBytesToSkip = numberOfBytesToSkip - self.version_string.string_length
            self.bytes = filereader.read_bytes(numberOfBytesToSkip)
        else:
            log.critical("Unsupported Map object version: %d", self.versionNumber)
            return

class RSEMAPRoomList(BinaryFileDataStructure):
    """Defines a list of rooms in the MAP"""
    def __init__(self):
        super(RSEMAPRoomList, self).__init__()

    def read(self, filereader: BinaryFileReader):
        raise NotImplementedError("This method is not implemented on this class as additional information is required. Please use read_room_list")

    def read_room_list(self, filereader: BinaryFileReader, gameVer: str):
        """
        Reads the list of rooms, based on game version for format change
        gameVer should be one of the constants in RSEGameVersions
        """
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_rooms(filereader, gameVer)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.roomListSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()
        self.section_string: SizedCString = SizedCString(filereader)

    def read_rooms(self, filereader: BinaryFileReader, gameVer: str):
        """
        Reads every room in list. Will read appropriate data structure for gameVer
        gameVer should be one of the constants in RSEGameVersions
        """
        self.roomCount: int = filereader.read_uint32()

        AnyRoomType = Union[R6MAPRoomDefinition, RSMAPRoomDefinition]
        self.rooms: List[AnyRoomType] = []
        for _ in range(self.roomCount):
            newObject: Optional[AnyRoomType] = None
            if gameVer == RSEGameVersions.RAINBOW_SIX:
                newObject = R6MAPRoomDefinition()
            if gameVer == RSEGameVersions.ROGUE_SPEAR:
                newObject = RSMAPRoomDefinition()

            if newObject is not None:
                newObject.read(filereader)
                self.rooms.append(newObject)
            else:
                log.critical("Unrecognised game version, skipping room")

class R6MAPRoomDefinition(BinaryFileDataStructure):
    """Defines a Room as used in Rainbow Six. Contains information such as levels and transitions"""
    def __init__(self):
        super(R6MAPRoomDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.id: int = filereader.read_uint32()
        self.version_string: SizedCString = SizedCString(filereader)
        self.versionNumber: int = filereader.read_uint32()

        self.name_string: SizedCString = SizedCString(filereader)

        self.unknown1: int = filereader.read_bytes(1)[0]
        self.unknown2: int = filereader.read_bytes(1)[0]
        if self.unknown1 == 0:
            self.unknown3: int = filereader.read_bytes(1)[0]

        self.shermanLevelCount: int = filereader.read_uint32()
        self.shermanLevels: List[R6MAPShermanLevelDefinition] = []
        for _ in range(self.shermanLevelCount):
            newObject = R6MAPShermanLevelDefinition()
            newObject.read(filereader)
            self.shermanLevels.append(newObject)

        self.transitionCount: int = filereader.read_uint32()
        self.transitions: List[R6MAPShermanLevelTransitionDefinition] = []
        for _ in range(self.transitionCount):
            tempTransition = R6MAPShermanLevelTransitionDefinition()
            tempTransition.read(filereader)
            self.transitions.append(tempTransition)

        self.levelHeightsCount: int = filereader.read_uint32()
        self.levelHeights: List[float] = filereader.read_vec_f(self.levelHeightsCount * 2)

        self.unknown5Count: int = filereader.read_uint32()
        self.unknown5: List[float] = filereader.read_vec_f(self.unknown5Count)

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

class R6MAPShermanLevelDefinition(BinaryFileDataStructure):
    """Contains a level definition as used in Rainbow Six"""
    def __init__(self):
        super(R6MAPShermanLevelDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.name_string: SizedCString = SizedCString(filereader)
        self.AABB: List[float] = filereader.read_vec_f(6)

        self.unknown2Count: int = filereader.read_uint32()
        self.unknown2: List[float] = filereader.read_vec_f(self.unknown2Count)

        self.hasShermanLevelPlanArea: int = filereader.read_bytes(1)[0]
        if self.hasShermanLevelPlanArea == 1:
            self.shermanLevelPlanArea: R6MAPShermanLevelPlanAreaDefinition = R6MAPShermanLevelPlanAreaDefinition()
            self.shermanLevelPlanArea.read(filereader)

    def get_aabb(self) -> AxisAlignedBoundingBox:
        """Calculate an Axis Align Bounding Box from the 2 corners/vertices of this level"""
        newBounds = AxisAlignedBoundingBox()
        newBounds.add_point(self.AABB[:3])
        newBounds.add_point(self.AABB[3:])
        return newBounds

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

#PETODO: this class and lower need to be annotated
class R6MAPShermanLevelPlanAreaDefinition(BinaryFileDataStructure):
    """This is related to the planning rendering, but exact details and usage is still TBD"""
    def __init__(self):
        super(R6MAPShermanLevelPlanAreaDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.unknown1 = filereader.read_uint32()
        self.ID = filereader.read_uint32()

        self.name_string = SizedCString(filereader)
        if self.name_string.string == "Version":
            self.version_string = self.name_string
            self.versionNumber = filereader.read_uint32()
            self.name_string = SizedCString(filereader)

        self.unknown2_bytes = filereader.read_bytes(4) #ABCD
        self.unknown3 = filereader.read_uint32() #U

        self.vertexCount = filereader.read_uint32()
        self.vertices = [] #coordinate
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.vertexParamCount = filereader.read_uint32()
        self.vertexParams = [] #coordinate2
        for _ in range(self.vertexParamCount):
            newParams = R6VertexParameterCollection()
            newParams.read(filereader)
            self.vertexParams.append(newParams)

        self.faceCount = filereader.read_uint32()
        self.faces = [] #coordinate3
        for _ in range(self.faceCount):
            newFace = R6FaceDefinition()
            newFace.read(filereader)
            self.faces.append(newFace)
        self.unknown5 = filereader.read_uint32()
        self.unknown6 = filereader.read_uint32()

        self.unknown_7_string = SizedCString(filereader)

        self.unknown8 = filereader.read_uint32()
        self.faceIndicesCount = filereader.read_uint32()
        self.faceIndices = filereader.read_vec_uint32(self.faceIndicesCount)

        self.unknown10 = filereader.read_uint32()
        self.unknown_11_string = SizedCString(filereader)
        self.unknown12 = filereader.read_uint32()

class RSMAPShermanLevelTransitionList(BinaryFileDataStructure):
    """This is related to the portal system and traversal between floors, but exact details and usage is still TBD"""
    def __init__(self):
        super(RSMAPShermanLevelTransitionList, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_transition_objects(filereader)

    def read_header_info(self, filereader):
        """Reads top level information for this data structure"""
        self.transitionListSize = filereader.read_uint32() #L, moved here to match other header structures
        self.ID = filereader.read_uint32()
        self.section_string = SizedCString(filereader)

    def read_transition_objects(self, filereader):
        """Reads the transition objects into a list"""
        self.transitionCount = filereader.read_uint32()
        self.transitions = []
        for _ in range(self.transitionCount):
            transition = RSMAPShermanLevelTransitionDefinition()
            transition.read(filereader)
            self.transitions.append(transition)

class RSMAPShermanLevelTransitionDefinition(BinaryFileDataStructure):
    """This is related to the portal system and traversal between floors, but exact details and usage is still TBD"""
    def __init__(self):
        super(RSMAPShermanLevelTransitionDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.name_string = SizedCString(filereader)
        log.debug(self.name_string.string)

        self.coords = filereader.read_vec_f(6)

class R6MAPShermanLevelTransitionDefinition(BinaryFileDataStructure):
    """This is related to the portal system and traversal between floors, but exact details and usage is still TBD"""
    def __init__(self):
        super(R6MAPShermanLevelTransitionDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.name_string = SizedCString(filereader)

        self.level_A_string = SizedCString(filereader)
        self.level_B_string = SizedCString(filereader)

        self.coords = filereader.read_vec_f(4)

class RSEMAPPlanningLevelList(BinaryFileDataStructure):
    """This is related to the planning levels, but exact details and usage is still TBD"""
    def __init__(self):
        super(RSEMAPPlanningLevelList, self).__init__()

    def read(self, filereader):
        raise NotImplementedError("This method is not implemented on this class as additional information is required. Please use read_planning_level_list")

    def read_planning_level_list(self, filereader, gameVer):
        """Reads the list of planning levels, based on game version for slight format change"""
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_planning_levels(filereader)

        if gameVer == RSEGameVersions.RAINBOW_SIX:
            self.unknown1 = filereader.read_bytes(1)[0] #Y

    def read_header_info(self, filereader):
        """Reads top level information for this data structure"""
        self.planningLevelListSize = filereader.read_uint32() #L, moved here to match other header structures
        self.ID = filereader.read_uint32()
        self.section_string = SizedCString(filereader)

    def read_planning_levels(self, filereader):
        """Reads the planning level objects into a list"""
        self.planningLevelCount = filereader.read_uint32()
        self.planningLevels = []
        for _ in range(self.planningLevelCount):
            planLevel = R6MAPPlanningLevelDefinition()
            planLevel.read(filereader)
            self.planningLevels.append(planLevel)

class R6MAPPlanningLevelDefinition(BinaryFileDataStructure):
    """This is related to the planning levels, but exact details and usage is still TBD"""
    def __init__(self):
        super(R6MAPPlanningLevelDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.levelNumber = filereader.read_float() #A
        self.floorHeight = filereader.read_float() #B
        self.roomCount = filereader.read_uint32()
        self.roomNames = []
        for _ in range(self.roomCount):
            string = SizedCString(filereader)
            self.roomNames.append(string)

class RSEMAPFooterDefinition(BinaryFileDataStructure):
    """Data stored at the end of a MAP file"""
    def __init__(self):
        super(RSEMAPFooterDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        self.end_map_string = SizedCString(filereader)
