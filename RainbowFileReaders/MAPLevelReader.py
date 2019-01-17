from FileUtilities import BinaryConversionUtilities
from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import RSEMaterialFormatConstants, RSEGameVersions, RSEGeometryFlags
from RainbowFileReaders.RSEGeometryDataStructures import RSEGeometryListHeader, R6GeometryObject
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader
from RainbowFileReaders.CXPMaterialPropertiesReader import load_relevant_cxps
from RainbowFileReaders.RSDMPLightReader import RSDMPLightFile

import pprint

from datetime import datetime

class MAPLevelFile(FileFormatReader):
    """Class to read full MAP files"""
    def __init__(self):
        super(MAPLevelFile, self).__init__()
        self.header = None
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []
        self.portalList = []
        self.lightList = []
        self.objectList = []

        self.footer = None
        #Game version is not stored in file, and has to be determined by analysing the structure of stored materials. Stored here for easy use
        self.gameVersion = None

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

        if len(self.materials) > 0:
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
        self.roomList.read(fileReader, self.gameVersion)

        if self.gameVersion == RSEGameVersions.ROGUE_SPEAR:
            self.transitionList = RSMAPShermanLevelTransitionList()
            self.transitionList.read(fileReader)

        self.planningLevelList = RSEMAPPlanningLevelList()
        self.planningLevelList.read(fileReader, self.gameVersion)

        self.mapFooter = RSEMAPFooterDefinition()
        self.mapFooter.read(fileReader)

        #read in DMP file data
        if self.gameVersion == RSEGameVersions.ROGUE_SPEAR:
            if self.filepath.lower().endswith(".map"):
                lightFileName = self.filepath[:-4] + ".dmp"
                lightFile = RSDMPLightFile()
                lightFile.read_file(lightFileName)
                self.dmpLights = lightFile

        return


class MAPHeader(BinaryFileDataStructure):
    def __init__(self):
        super(MAPHeader, self).__init__()
        self.time = datetime.now()
        self.timePOSIXRaw = 0

    def read(self, filereader):
        super().read(filereader)

        self.read_named_string(filereader, "headerBeginMessage")
        self.timePOSIXRaw = filereader.read_uint()
        #special case handling, some files have a zero timestamp recorded, which datetime.fromtimestamp() doesn't like
        if self.timePOSIXRaw == 0:
            self.time = datetime(1970,1,1)
        else:
            self.time = datetime.fromtimestamp(self.timePOSIXRaw)

class RSMAPGeometryObject(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPGeometryObject, self).__init__()
    
    def read(self, filereader):
        super().read(filereader)
        
        self.size = filereader.read_uint()
        self.id = filereader.read_uint()
        
        self.read_version_string(filereader)
        self.versionNumber = filereader.read_uint()

        self.read_name_string(filereader)

        self.geometryData = RSMAPGeometryData()
        self.geometryData.read(filereader)


class RSMAPGeometryData(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPGeometryData, self).__init__()
        self.size = None
        self.ID = None
        self.versionStringLength = None
        self.versionNumber = None
        self.versionString = None
        self.nameStringLength = None
        self.nameStringRaw = None
        self.nameString = None

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)

        self.read_vertices(filereader)

        self.read_face_groups(filereader)

        self.collisionInformation = RSMAPCollisionInformation()
        self.collisionInformation.read(filereader)

    def read_header_info(self, filereader):
        self.size = filereader.read_uint()
        self.id = filereader.read_uint()
        
        self.read_version_string(filereader)
        self.versionNumber = filereader.read_uint()

        self.read_name_string(filereader)

    def read_vertices(self, filereader):
        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

    def read_face_groups(self, filereader):
        self.faceGroupCount = filereader.read_uint()
        self.faceGroups = []

        for _ in range(self.faceGroupCount):
            newFaceGroup = RSMAPFaceGroup()
            newFaceGroup.read(filereader)
            self.faceGroups.append(newFaceGroup)


class RSMAPFaceGroup(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPFaceGroup, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.materialIndex = filereader.read_uint()

        self.faceCount = filereader.read_uint()
        
        self.faceNormals = []
        self.faceDistancesFromOrigin = []

        for _ in range(self.faceCount):
            self.faceNormals.append(filereader.read_vec_f(3))
            self.faceDistancesFromOrigin.append(filereader.read_float())

        self.faceVertexIndices = []
        for _ in range(self.faceCount):
            self.faceVertexIndices.append(filereader.read_vec_short_uint(3))

        self.faceVertexParamIndices = []
        for _ in range(self.faceCount):
            self.faceVertexParamIndices.append(filereader.read_vec_short_uint(3))

        self.vertexParams = RSMAPVertexParameterCollection()
        self.vertexParams.read(filereader)


class RSMAPVertexParameterCollection(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPVertexParameterCollection, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.vertexParamCount = filereader.read_uint()

        self.normals = []
        for _ in range(self.vertexParamCount):
            self.normals.append(filereader.read_vec_f(3))

        self.UVs = []
        for _ in range(self.vertexParamCount):
            self.UVs.append(filereader.read_vec_f(2))
        
        self.colors = []
        for _ in range(self.vertexParamCount):
            self.colors.append(filereader.read_vec_f(4))

class RSMAPCollisionInformation(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPCollisionInformation, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.vertexCount = filereader.read_uint()

        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.normalCount = filereader.read_uint()

        self.normals = []
        self.faceDistancesFromOrigin = []

        for _ in range(self.normalCount):
            self.normals.append(filereader.read_vec_f(3))
            self.faceDistancesFromOrigin.append(filereader.read_float())

        self.faceCount = filereader.read_uint()
        # self.unknown2IndexCollection = []
        # for _ in range(self.faceCount):
        #     self.unknown2IndexCollection.append(filereader.read_vec_short_uint(8))

        self.faces = []
        for _ in range(self.faceCount):
            faceObject = RSMAPCollisionFaceInformation()
            faceObject.read(filereader)
            self.faces.append(faceObject)

        self.collisionMeshDefinitionsCount = filereader.read_uint()
        self.collisionMeshDefinitions = []
        for _ in range(self.collisionMeshDefinitionsCount):
            dataObject = RSMAPCollisionMesh()
            dataObject.read(filereader)
            self.collisionMeshDefinitions.append(dataObject)

class RSMAPCollisionFaceInformation(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPCollisionFaceInformation, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.vertexIndices = filereader.read_vec_short_uint(3)

        self.unknown1 = filereader.read_short_uint()

        self.normalIndices = filereader.read_vec_short_uint(3)

        self.unknown2 = filereader.read_short_uint()


class RSMAPCollisionMesh(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPCollisionMesh, self).__init__()
    
    def read(self, filereader):
        super().read(filereader)

        self.read_name_string(filereader)

        self.geometryFlags = filereader.read_uint() #??
        self.geometryFlagsEvaluated = RSEGeometryFlags.EvaluateFlags(self.geometryFlags)

        self.faceCount = filereader.read_uint()
        self.faceIndices = filereader.read_vec_short_uint(self.faceCount)

class RSEMAPPortalList(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPPortalList, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_portals(filereader)

    def read_header_info(self, filereader):
        self.portalListSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.read_section_string(filereader)

    def read_portals(self, filereader):
        self.portalCount = filereader.read_uint()
        self.portals = []
        for _ in range(self.portalCount):
            newPortal = RSEMAPPortal()
            newPortal.read(filereader)
            self.portals.append(newPortal)

class RSEMAPPortal(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPPortal, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.portalSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.read_version_string(filereader)
        self.versionNumber = filereader.read_uint()

        self.read_name_string(filereader)

        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.roomA = filereader.read_uint()
        self.roomB = filereader.read_uint()


class R6MAPLightList(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPLightList, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_lights(filereader)

    def read_header_info(self, filereader):
        self.lightListSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.read_section_string(filereader)

    def read_lights(self, filereader):
        self.lightCount = filereader.read_uint()

        self.lights = []
        for _ in range(self.lightCount):
            newLight = R6MAPLight()
            newLight.read(filereader)
            self.lights.append(newLight)



class R6MAPLight(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPLight, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        
        self.lightSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        #Some maps store a version string, others don't, not quite sure why. Also makes unknown6 quite unclear as to whether they are separate fields or not
        self.read_name_string(filereader)
        if self.nameString == "Version":
            self.versionString = self.nameString
            self.versionStringRaw = self.nameStringRaw
            self.versionStringLength = self.nameStringLength
            self.versionNumber = filereader.read_uint()

            self.read_name_string(filereader)
            self.unknown6 = filereader.read_uint()
        else:
            self.unknown6 = filereader.read_bytes(3)

        #3x3 matrix = 9 elements
        self.transformMatrix = filereader.read_vec_f(9)

        self.position = filereader.read_vec_f(3)
        self.color = filereader.read_vec_uint(3)
        self.constantAttenuation = filereader.read_float()
        self.linearAttenuation = filereader.read_float()
        self.quadraticAttenuation = filereader.read_float()
        #maybe?
        self.falloff = filereader.read_float()
        self.energy = filereader.read_float()
        self.type = filereader.read_bytes(1)[0]

class RSEMAPObjectList(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPObjectList, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_objects(filereader)

    def read_header_info(self, filereader):
        self.objectListSize = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.read_section_string(filereader)

    def read_objects(self, filereader):
        self.objectCount = filereader.read_uint()

        self.objects = []
        for _ in range(self.objectCount):
            newObject = RSEMAPObject()
            newObject.read(filereader)
            self.objects.append(newObject)

class RSEMAPObject(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPObject, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        RS_OBJECT_VERSION = 5
        R6_OBJECT_VERSION = 1

        self.objectSize = filereader.read_uint()
        self.objectType = filereader.read_uint()
        self.read_version_string(filereader)
        self.versionNumber = filereader.read_uint()
        self.read_name_string(filereader)

        if self.versionNumber >= RS_OBJECT_VERSION:
            self.bytes = filereader.read_bytes(self.objectSize)
        elif self.versionNumber == R6_OBJECT_VERSION:
            numberOfBytesToSkip = self.objectSize
            #skip 4 uints
            numberOfBytesToSkip = numberOfBytesToSkip - 4*4
            #skip the length of the 2 strings
            numberOfBytesToSkip = numberOfBytesToSkip - self.nameStringLength
            numberOfBytesToSkip = numberOfBytesToSkip - self.versionStringLength
            self.bytes = filereader.read_bytes(numberOfBytesToSkip)
        else:
            print("BIG ERROR UNSUPPORTED OBJECT VERSION: " + str(self.versionNumber))
            return
        return

        self.read_name_string(filereader)
        self.read_named_string(filereader, "filenameString")

        #3x3 matrix = 9 elements
        self.transformMatrix = filereader.read_vec_f(9)

        self.position = filereader.read_vec_f(3)

        self.read_named_string(filereader, "unknownString")
        self.read_named_string(filereader, "hitsoundAssetString")
        self.read_named_string(filereader, "debrisParticleAssetString")

class RSEMAPRoomList(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPRoomList, self).__init__()

    def read(self, filereader, gameVer):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_rooms(filereader, gameVer)

    def read_header_info(self, filereader):
        self.roomListSize = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.read_section_string(filereader)

    def read_rooms(self, filereader, gameVer):
        self.roomCount = filereader.read_uint()

        self.rooms = []
        for _ in range(self.roomCount):
            if gameVer == RSEGameVersions.RAINBOW_SIX:
                newObject = R6MAPRoomDefinition()
            if gameVer == RSEGameVersions.ROGUE_SPEAR:
                newObject = RSMAPRoomDefinition()
            newObject.read(filereader)
            self.rooms.append(newObject)

class R6MAPRoomDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPRoomDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        
        self.ID = filereader.read_uint()
        self.read_version_string(filereader)
        self.versionNumber = filereader.read_uint()

        self.read_name_string(filereader)

        self.unknown1 = filereader.read_bytes(1)[0]
        self.unknown2 = filereader.read_bytes(1)[0]
        if(self.unknown1 == 0):
            self.unknown3 = filereader.read_bytes(1)[0]

        self.shermanLevelCount = filereader.read_uint()
        self.shermanLevels = []
        for _ in range(self.shermanLevelCount):
            newObject = R6MAPShermanLevelDefinition()
            newObject.read(filereader)
            self.shermanLevels.append(newObject)

        self.transitionCount = filereader.read_uint()
        self.transitions = []
        for _ in range(self.transitionCount):
            tempTransition = R6MAPShermanLevelTransitionDefinition()
            tempTransition.read(filereader)
            self.transitions.append(tempTransition)

        self.unknown4Count = filereader.read_uint()
        self.unknown4 = filereader.read_vec_f(self.unknown4Count * 2)

        self.unknown5Count = filereader.read_uint()
        self.unknown5 = filereader.read_vec_f(self.unknown5Count)

class RSMAPRoomDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPRoomDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        
        self.ID = filereader.read_uint()
        self.read_version_string(filereader)
        self.versionNumber = filereader.read_uint()

        self.read_name_string(filereader)

        self.unknown1 = filereader.read_bytes(1)[0] #A
        self.unknown2 = filereader.read_bytes(1)[0] #B
        self.unknown3 = filereader.read_bytes(1)[0] #C
        if self.unknown1 == 0:
            self.unknown4 = filereader.read_bytes(1)[0] #D

        if self.unknown3 == 1:
            self.unknown5 = filereader.read_vec_f(6)
        
        if hasattr(self, 'unknown4') and self.unknown4 == 1:
            self.unknown6 = filereader.read_vec_f(6)

        self.shermanLevelCount = filereader.read_uint()
        self.shermanLevels = []
        for _ in range(self.shermanLevelCount):
            newObject = RSMAPShermanLevelDefinition()
            newObject.read(filereader)
            self.shermanLevels.append(newObject)


        self.unknown4Count = filereader.read_uint()

        self.unknown5 = filereader.read_float()
        self.unknown4 = []
        for _ in range(self.unknown4Count):
            newUnknown4 = filereader.read_vec_f(2)
            self.unknown4.append(newUnknown4)

class R6MAPShermanLevelDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPShermanLevelDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_name_string(filereader)
        self.unknown1 = filereader.read_vec_f(6)
        
        self.unknown2Count = filereader.read_uint()
        self.unknown2 = filereader.read_vec_f(self.unknown2Count)

        self.unknown3 = filereader.read_bytes(1)[0]
        if self.unknown3 == 1:
            self.unknown3Struct = R6MAPShermanLevelPlanAreaDefinition()
            self.unknown3Struct.read(filereader)

class RSMAPShermanLevelDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPShermanLevelDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_name_string(filereader)
        self.transformCount = filereader.read_uint() # ACount
        self.transforms = []
        for _ in range(self.transformCount):
            transformObj = RSMAPShermanLevelTransformInformation()
            transformObj.read(filereader)
            self.transforms.append(transformObj)
        
        self.unknown3Count = filereader.read_uint()
        self.unknown3 = filereader.read_vec_f(self.unknown3Count)

        self.unknown4 = filereader.read_bytes(1)[0]

class RSMAPShermanLevelTransformInformation(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPShermanLevelTransformInformation, self).__init__()

    def read(self, filereader):
        super().read(filereader) 

        #3x3 matrix = 9 elements
        self.transformMatrix = filereader.read_vec_f(9)
        self.position = filereader.read_vec_f(3)
        self.unknown2 = filereader.read_vec_f(6) #size?

class R6MAPShermanLevelPlanAreaDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPShermanLevelPlanAreaDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.unknown1 = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.read_name_string(filereader)
        if self.nameString == "Version":
            self.versionString = self.nameString
            self.versionStringRaw = self.nameStringRaw
            self.versionStringLength = self.nameStringLength
            self.versionNumber = filereader.read_uint()

            self.read_name_string(filereader)

        self.unknown2_bytes = filereader.read_bytes(4) #ABCD
        self.unknown3 = filereader.read_uint() #U

        self.vertexCount = filereader.read_uint()
        self.vertices = [] #coordinate
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.vertexParamCount = filereader.read_uint()
        self.vertexParams = [] #coordinate2
        for _ in range(self.vertexParamCount):
            self.vertexParams.append(filereader.read_vec_f(9))

        self.unknown4Count = filereader.read_uint()
        self.unknown4DataStructs = [] #coordinate3
        for _ in range(self.unknown4Count):
            self.unknown4DataStructs.append(filereader.read_vec_uint(11))
        self.unknown5 = filereader.read_uint()
        self.unknown6 = filereader.read_uint()

        self.read_named_string(filereader, "Unknown7String")

        self.unknown8 = filereader.read_uint()
        self.unknown9Count = filereader.read_uint()
        self.unknown9 = filereader.read_vec_uint(self.unknown9Count)

        self.unknown10 = filereader.read_uint()
        self.read_named_string(filereader, "Unknown11String")
        self.unknown12 = filereader.read_uint()

class RSMAPShermanLevelTransitionList(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPShermanLevelTransitionList, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_transition_objects(filereader)

    def read_header_info(self, filereader):
        self.transitionListSize = filereader.read_uint() #L, moved here to match other header structures
        self.ID = filereader.read_uint()
        self.read_section_string(filereader)

    def read_transition_objects(self, filereader):
        self.transitionCount = filereader.read_uint()
        self.transitions = []
        for _ in range(self.transitionCount):
            transition = RSMAPShermanLevelTransitionDefinition()
            transition.read(filereader)
            self.transitions.append(transition)

class RSMAPShermanLevelTransitionDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPShermanLevelTransitionDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_name_string(filereader)
        print(self.nameString)

        self.coords = filereader.read_vec_f(6)

class R6MAPShermanLevelTransitionDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPShermanLevelTransitionDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_name_string(filereader)

        self.read_named_string(filereader, "levelAString")
        self.read_named_string(filereader, "levelBString")

        self.coords = filereader.read_vec_f(4)

class RSEMAPPlanningLevelList(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPPlanningLevelList, self).__init__()

    def read(self, filereader, gameVer):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_planning_levels(filereader)

        if gameVer == RSEGameVersions.RAINBOW_SIX:
            self.unknown1 = filereader.read_bytes(1)[0] #Y

    def read_header_info(self, filereader):
        self.planningLevelListSize = filereader.read_uint() #L, moved here to match other header structures
        self.ID = filereader.read_uint()
        self.read_section_string(filereader)

    def read_planning_levels(self, filereader):
        self.planningLevelCount = filereader.read_uint()
        self.planningLevels = []
        for _ in range(self.planningLevelCount):
            planLevel = R6MAPPlanningLevelDefinition()
            planLevel.read(filereader)
            self.planningLevels.append(planLevel)

class R6MAPPlanningLevelDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6MAPPlanningLevelDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.unknown1 = filereader.read_float() #A
        self.unknown2 = filereader.read_float() #B
        self.nameCount = filereader.read_uint()
        self.names = []
        for _ in range(self.nameCount):
            string = SerializedCString()
            string.read(filereader)
            self.names.append(string)

class SerializedCString(BinaryFileDataStructure):
    def __init__(self):
        super(SerializedCString, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        self.read_name_string(filereader)

class RSEMAPFooterDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPFooterDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        self.read_named_string(filereader, "EndMapString")
