from RainbowFileReaders import BinaryConversionUtilities
from RainbowFileReaders.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import RSEMaterialFormatConstants, RSEGameVersions
from RainbowFileReaders.SOBModelReader import RSEGeometryListHeader, SOBGeometryObject
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader

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
        self.footer = None
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

        self.materials = []
        for _ in range(self.materialListHeader.numMaterials):
            newMaterial = RSEMaterialDefinition()
            newMaterial.read(fileReader)
            self.materials.append(newMaterial)
            if self.verboseOutput:
                pass
                #newMaterial.print_structure_info()

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
                newObj = SOBGeometryObject()
                newObj.read(fileReader)
                self.geometryObjects.append(newObj)
                if self.verboseOutput:
                    pass

        self.portalList = RSEMAPPortalList()
        self.portalList.read(fileReader)

        self.lightList = RSEMAPLightList()
        self.lightList.read(fileReader)

        self.objectList = RSEMAPObjectList()
        self.objectList.read(fileReader)

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
        
        self.versionLength = filereader.read_uint()
        self.versionStringRaw = filereader.read_bytes(self.versionLength)
        self.versionString = self.versionStringRaw[:-1].decode("utf-8")

        self.versionNumber = filereader.read_uint()

        self.nameLength = filereader.read_uint()
        self.nameStringRaw = filereader.read_bytes(self.nameLength)
        self.nameString = self.nameStringRaw[:-1].decode("utf-8")

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
        self.objectNameLength = None
        self.objectNameRaw = None
        self.objectName = None

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)

        self.read_vertices(filereader)

        self.read_face_groups(filereader)

        self.collisionInformation = RSMAP2DCollisionInformation()
        self.collisionInformation.read(filereader)

        self.unknownDataStructure = RSMAPUnknownGeometryDataSection()
        self.unknownDataStructure.read(filereader)

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

        self.unknown1 = filereader.read_uint()

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
        self.normal = None
        self.UV = None
        self.color = None

    def read(self, filereader):
        super().read(filereader)

        self.vertexCount = filereader.read_uint()

        self.normals = []
        for _ in range(self.vertexCount):
            self.normals.append(filereader.read_vec_f(3))

        self.UVs = []
        for _ in range(self.vertexCount):
            self.UVs.append(filereader.read_vec_f(2))
        
        self.colors = []
        for _ in range(self.vertexCount):
            self.colors.append(filereader.read_vec_f(4))

class RSMAP2DCollisionInformation(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAP2DCollisionInformation, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.vertexCount = filereader.read_uint()

        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        self.faceCount = filereader.read_uint()

        self.faceNormals = []
        self.faceDistancesFromOrigin = []

        for _ in range(self.faceCount):
            self.faceNormals.append(filereader.read_vec_f(3))
            self.faceDistancesFromOrigin.append(filereader.read_float())

class RSMAPUnknownGeometryDataSection(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPUnknownGeometryDataSection, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.unknown2Count = filereader.read_uint()
        self.unknown2IndexCollection = []
        for _ in range(self.unknown2Count):
            self.unknown2IndexCollection.append(filereader.read_vec_short_uint(8))
        
        self.unknownDataObjectCount = filereader.read_uint()
        self.unknownDataObjects = []
        for _ in range(self.unknownDataObjectCount):
            dataObject = RSMAPUnknownGeometryDataObject()
            dataObject.read(filereader)
        
class RSMAPUnknownGeometryDataObject(BinaryFileDataStructure):
    def __init__(self):
        super(RSMAPUnknownGeometryDataObject, self).__init__()
    
    def read(self, filereader):
        super().read(filereader)

        self.read_name_string(filereader)

        self.unknown4 = filereader.read_uint()

        self.unknown5Count = filereader.read_uint()
        self.unknown5Indices = filereader.read_vec_short_uint(self.unknown5Count)

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


class RSEMAPLightList(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPLightList, self).__init__()

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
            newLight = RSEMAPLight()
            newLight.read(filereader)
            self.lights.append(newLight)



class RSEMAPLight(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPLight, self).__init__()

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
        self.unknown7 = filereader.read_float()
        self.unknown8 = filereader.read_uint()
        self.unknown9 = filereader.read_float()
        #maybe?
        self.falloff = filereader.read_float()
        self.attenuation = filereader.read_float()
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