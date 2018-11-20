from RainbowFileReaders import BinaryConversionUtilities
from RainbowFileReaders.BinaryConversionUtilities import BinaryFileDataStructure
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import RSEMaterialFormatConstants, RSEGameVersions
from RainbowFileReaders.SOBModelReader import RSEGeometryListHeader, SOBGeometryObject
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader

import pprint

from datetime import datetime

class MAPLevelFile(BinaryFileDataStructure):
    """Class to read full SOB files"""
    def __init__(self):
        super(MAPLevelFile, self).__init__()
        self.header = None
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []
        self.footer = None
        self.gameVersion = None

    def read_map(self, filename, verboseOutput=False):
        mapFile = BinaryConversionUtilities.BinaryFileReader(filename)

        self.header = MAPHeader()
        self.header.read(mapFile)
        if verboseOutput:
            self.header.print_header_info()

        self.materialListHeader = RSEMaterialListHeader()
        self.materialListHeader.read(mapFile)
        if verboseOutput:
            self.materialListHeader.print_structure_info()

        self.materials = []
        for _ in range(self.materialListHeader.numMaterials):
            newMaterial = RSEMaterialDefinition()
            newMaterial.read(mapFile)
            self.materials.append(newMaterial)
            if verboseOutput:
                pass
                #newMaterial.print_material_info()

        if len(self.materials) > 0:
            self.gameVersion = self.materials[0].get_material_game_version()

        self.geometryListHeader = RSEGeometryListHeader()
        self.geometryListHeader.read(mapFile)
        if verboseOutput:
            self.geometryListHeader.print_header_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            if self.gameVersion == RSEGameVersions.ROGUE_SPEAR:
                newObj = RSMAPGeometryObject()
                newObj.read(mapFile)
                self.geometryObjects.append(newObj)
                if verboseOutput:
                    pass
            else:
                newObj = SOBGeometryObject()
                newObj.read(mapFile)
                self.geometryObjects.append(newObj)
                if verboseOutput:
                    pass

        print("== Finished Processing: " + str(filename))

        return

        self.footer = SOBFooterDefinition()
        self.footer.read_footer(mapFile)
        
        print("Processed: " + str(mapFile.get_seekg()) + " bytes")
        print("Length: " + str(mapFile.get_length()) + " bytes")
        print("Unprocessed: " + str(mapFile.get_length() - mapFile.get_seekg()) + " bytes")


class MAPHeader(BinaryFileDataStructure):
    def __init__(self):
        super(MAPHeader, self).__init__()
        self.headerLength = 0
        self.headerBeginMessage = None
        self.time = datetime.now()
        self.timePOSIXRaw = 0

    def read(self, filereader):
        super().read(filereader)

        self.headerLength = filereader.read_uint()
        self.headerBeginMessageRaw = filereader.read_bytes(self.headerLength)
        self.headerBeginMessage = self.headerBeginMessageRaw[:-1].decode("utf-8")
        self.timePOSIXRaw = filereader.read_uint()
        #special case handling, some files have a zero timestamp recorded, which datetime.fromtimestamp() doesn't like
        if self.timePOSIXRaw == 0:
            self.time = datetime(1970,1,1)
        else:
            self.time = datetime.fromtimestamp(self.timePOSIXRaw)

    def print_header_info(self):
        print("Header length: " + str(self.headerLength))
        print("Header message: " + str(self.headerBeginMessage))
        print("Saved time: " + str(self.time.strftime('%d/%m/%Y %H:%M:%S')))
        print("")

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


    def print_object_info(self):
        pprint.pprint(vars(self))


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
        
        self.versionLength = filereader.read_uint()

        self.versionStringRaw = filereader.read_bytes(self.versionLength)
        self.versionString = self.versionStringRaw[:-1].decode("utf-8")

        self.versionNumber = filereader.read_uint()

        self.objectNameLength = filereader.read_uint()
        self.objectNameRaw = filereader.read_bytes(self.objectNameLength)
        self.objectName = self.objectNameRaw[:-1].decode("utf-8")

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

        self.nameLength = filereader.read_uint()
        self.nameStringRaw = filereader.read_bytes(self.nameLength)
        self.nameString = self.nameStringRaw[:-1].decode("utf-8")

        self.unknown4 = filereader.read_uint()

        self.unknown5Count = filereader.read_uint()
        self.unknown5Indices = filereader.read_vec_short_uint(self.unknown5Count)

class RSEMAPPortalList(BinaryFileDataStructure):
    def __init__(self):
        super(RSEMAPPortalList, self).__init__()
