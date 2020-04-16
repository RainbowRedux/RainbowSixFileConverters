"""
This module defines the fileformat and data structures specific to MAP files used in Rainbow Six and Rogue Spear
"""
from __future__ import annotations
import logging
from typing import List, Union, Optional
from datetime import datetime

from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader, SizedCString, BinaryFileReader
from RainbowFileReaders import R6Settings, R6Constants
from RainbowFileReaders.R6Constants import RSEGameVersions
from RainbowFileReaders.RSEGeometryDataStructures import RSEGeometryListHeader, R6GeometryObject
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader
from RainbowFileReaders.CXPMaterialPropertiesReader import load_relevant_cxps
from RainbowFileReaders.RSDMPLightReader import RSDMPLightFile
from RainbowFileReaders.MathHelpers import Vector, IntIterable
from RainbowFileReaders.RenderableArray import RenderableArray
from RainbowFileReaders.R6MAPStructures import R6MAPRoomDefinition, R6MAPLightList, R6MAPPlanningLevelDefinition
from RainbowFileReaders.RSMAPStructures import RSMAPRoomDefinition, RSMAPGeometryObject, RSMAPShermanLevelTransitionList

log = logging.getLogger(__name__)

AnyRoomType = Union[R6MAPRoomDefinition, RSMAPRoomDefinition]

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
        self.lightList: R6MAPLightList = []
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
        triangleIndices: List[IntIterable] = [ [0,1,2],
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
        for _ in range(len(currentRenderable.vertices)):
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

        self.RS_OBJECT_VERSION: int = 5
        self.R6_OBJECT_VERSION: int = 1

        self.bytes: bytes = b''

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.objectSize: int = filereader.read_uint32()
        self.objectType: int = filereader.read_uint32()
        self.version_string: SizedCString = SizedCString(filereader)
        self.versionNumber: int = filereader.read_uint32()
        self.name_string: SizedCString = SizedCString(filereader)

        if self.versionNumber >= self.RS_OBJECT_VERSION:
            self.bytes = filereader.read_bytes(self.objectSize)
        elif self.versionNumber == self.R6_OBJECT_VERSION:
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

class RSEMAPPlanningLevelList(BinaryFileDataStructure):
    """This is related to the planning levels, but exact details and usage is still TBD"""
    def __init__(self):
        super(RSEMAPPlanningLevelList, self).__init__()

    def read(self, filereader: BinaryFileReader):
        raise NotImplementedError("This method is not implemented on this class as additional information is required. Please use read_planning_level_list")

    def read_planning_level_list(self, filereader: BinaryFileReader, gameVer: str):
        """
        Reads the list of planning levels, based on game version for slight format change
        gameVer should be a constant from RSEGameVersions
        """
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_planning_levels(filereader)

        if gameVer == RSEGameVersions.RAINBOW_SIX:
            self.unknown1: int = filereader.read_bytes(1)[0] #Y

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.planningLevelListSize: int = filereader.read_uint32() #L, moved here to match other header structures
        self.id: int = filereader.read_uint32()
        self.section_string: SizedCString = SizedCString(filereader)

    def read_planning_levels(self, filereader: BinaryFileReader):
        """Reads the planning level objects into a list"""
        self.planningLevelCount: int = filereader.read_uint32()
        self.planningLevels: List[R6MAPPlanningLevelDefinition] = []
        for _ in range(self.planningLevelCount):
            planLevel = R6MAPPlanningLevelDefinition()
            planLevel.read(filereader)
            self.planningLevels.append(planLevel)

class RSEMAPFooterDefinition(BinaryFileDataStructure):
    """Data stored at the end of a MAP file"""
    def __init__(self):
        super(RSEMAPFooterDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)
        self.end_map_string: SizedCString = SizedCString(filereader)
