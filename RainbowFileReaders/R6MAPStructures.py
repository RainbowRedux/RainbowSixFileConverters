"""Contains data structures specific to Rainbow Six (1998) maps"""

from typing import List

from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, BinaryFileReader, SizedCString
from RainbowFileReaders.MathHelpers import AxisAlignedBoundingBox
from RainbowFileReaders.RSEGeometryDataStructures import R6VertexParameterCollection, R6FaceDefinition

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

class R6MAPShermanLevelPlanAreaDefinition(BinaryFileDataStructure):
    """This is related to the planning rendering, but exact details and usage is still TBD"""
    def __init__(self):
        super(R6MAPShermanLevelPlanAreaDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.unknown1: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()

        self.name_string: SizedCString = SizedCString(filereader)
        if self.name_string.string == "Version":
            self.version_string: SizedCString = self.name_string
            self.versionNumber: int = filereader.read_uint32()
            self.name_string = SizedCString(filereader)

        self.unknown2_bytes: bytes = filereader.read_bytes(4) #ABCD
        self.unknown3: int = filereader.read_uint32() #U

        self.vertexCount: int = filereader.read_uint32()
        self.vertices: List[List[float]] = [] #coordinate
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.vertexParamCount: int = filereader.read_uint32()
        self.vertexParams: List[R6VertexParameterCollection] = [] #coordinate2
        for _ in range(self.vertexParamCount):
            newParams = R6VertexParameterCollection()
            newParams.read(filereader)
            self.vertexParams.append(newParams)

        self.faceCount: int = filereader.read_uint32()
        self.faces: List[R6FaceDefinition] = [] #coordinate3
        for _ in range(self.faceCount):
            newFace = R6FaceDefinition()
            newFace.read(filereader)
            self.faces.append(newFace)
        self.unknown5: int = filereader.read_uint32()
        self.unknown6: int = filereader.read_uint32()

        self.unknown_7_string: SizedCString = SizedCString(filereader)

        self.unknown8: int = filereader.read_uint32()
        self.faceIndicesCount: int = filereader.read_uint32()
        self.faceIndices: List[int] = filereader.read_vec_uint32(self.faceIndicesCount)

        self.unknown10: int = filereader.read_uint32()
        self.unknown_11_string: SizedCString = SizedCString(filereader)
        self.unknown12: int = filereader.read_uint32()

class R6MAPShermanLevelTransitionDefinition(BinaryFileDataStructure):
    """This is related to the portal system and traversal between floors, but exact details and usage is still TBD"""
    def __init__(self):
        super(R6MAPShermanLevelTransitionDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.name_string: SizedCString = SizedCString(filereader)

        self.level_A_string: SizedCString = SizedCString(filereader)
        self.level_B_string: SizedCString = SizedCString(filereader)

        self.coords = filereader.read_vec_f(4)

class R6MAPPlanningLevelDefinition(BinaryFileDataStructure):
    """This is related to the planning levels, but exact details and usage is still TBD"""
    def __init__(self):
        super(R6MAPPlanningLevelDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.levelNumber: float = filereader.read_float() #A
        self.floorHeight: float = filereader.read_float() #B
        self.roomCount: int = filereader.read_uint32()
        self.roomNames: List[SizedCString] = []
        for _ in range(self.roomCount):
            string = SizedCString(filereader)
            self.roomNames.append(string)
