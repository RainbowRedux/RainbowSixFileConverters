from RainbowFileReaders import BinaryConversionUtilities
from RainbowFileReaders import R6Settings
from RainbowFileReaders.SOBModelReader import RSEMaterialListHeader, RSEMaterialDefinition, RSEGeometryListHeader, SOBGeometryObject

import pprint


#from RainbowFileReaders.SOBModelReader import SOBVertexParameterCollection

from datetime import datetime

class MAPLevelFile(object):
    """Class to read full SOB files"""
    def __init__(self):
        super(MAPLevelFile, self).__init__()
        self.header = None
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []
        self.footer = None

    def read_map(self, filename, verboseOutput=False):
        mapFile = BinaryConversionUtilities.BinaryFileReader(filename)

        self.header = MAPHeader()
        self.header.read_header(mapFile)
        if verboseOutput:
            self.header.print_header_info()

        self.materialListHeader = RSEMaterialListHeader()
        self.materialListHeader.read_header(mapFile)
        if verboseOutput:
            self.materialListHeader.print_header_info()

        self.materials = []
        for _ in range(self.materialListHeader.numMaterials):
            newMaterial = RSEMaterialDefinition()
            newMaterial.read_material(mapFile)
            self.materials.append(newMaterial)
            if verboseOutput:
                pass
                #newMaterial.print_material_info()

        self.geometryListHeader = RSEGeometryListHeader()
        self.geometryListHeader.read_header(mapFile)
        if verboseOutput:
            self.geometryListHeader.print_header_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            newObj = RSMAPExpandedGeometryObject()
            newObj.read_object(mapFile)
            self.geometryObjects.append(newObj)
            if verboseOutput:
                pass
                newObj.print_object_info()
        
        return

        self.footer = SOBFooterDefinition()
        self.footer.read_footer(mapFile)
        
        print("Processed: " + str(mapFile.get_seekg()) + " bytes")
        print("Length: " + str(mapFile.get_length()) + " bytes")
        print("Unprocessed: " + str(mapFile.get_length() - mapFile.get_seekg()) + " bytes")


class MAPHeader(object):
    def __init__(self):
        super(MAPHeader, self).__init__()
        self.headerLength = 0
        self.headerBeginMessage = None
        self.time = datetime.now()
        self.timePOSIXRaw = 0

    def read_header(self, filereader):
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

class RSMAPExpandedGeometryObject(object):
    def __init__(self):
        super(RSMAPExpandedGeometryObject, self).__init__()
    
    def read_object(self, filereader):
        self.size = filereader.read_uint()
        self.id = filereader.read_uint()
        
        self.versionLength = filereader.read_uint()
        self.versionStringRaw = filereader.read_bytes(self.versionLength)
        self.versionString = self.versionStringRaw[:-1].decode("utf-8")

        self.versionNumber = filereader.read_uint()

        self.nameLength = filereader.read_uint()
        self.nameStringRaw = filereader.read_bytes(self.nameLength)
        self.nameString = self.nameStringRaw[:-1].decode("utf-8")

        print("Reading geometry header")
        print("Byte Address: " + str(filereader.get_seekg()))
        self.geometryObjectHeader = RSMAPGeometryObjectHeader()
        self.geometryObjectHeader.read_header(filereader)
        print("Read geometry header")

        pass

    def print_object_info(self):
        pprint.pprint(vars(self))


class RSMAPGeometryObjectHeader(object):
    def __init__(self):
        super(RSMAPGeometryObjectHeader, self).__init__()
        self.size = None
        self.ID = None
        self.versionStringLength = None
        self.versionNumber = None
        self.versionString = None
        self.objectNameLength = None
        self.objectNameRaw = None
        self.objectName = None

    def read_header(self, filereader):
        self.size = filereader.read_uint()
        self.id = filereader.read_uint()
        
        self.versionLength = filereader.read_uint()

        self.versionStringRaw = filereader.read_bytes(self.versionLength)
        self.versionString = self.versionStringRaw[:-1].decode("utf-8")

        self.versionNumber = filereader.read_uint()

        self.nameLength = filereader.read_uint()
        self.nameStringRaw = filereader.read_bytes(self.nameLength)
        self.nameString = self.nameStringRaw[:-1].decode("utf-8")
        print("objectName: " + self.nameString)

        self.read_vertices(filereader)

        self.read_face_groups(filereader)

        #self.read_faces(filereader)

        print("==================================")

    def read_vertices(self, filereader):
        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        print("Number of vertices read: " + str(len(self.vertices)))

    def read_face_groups(self, filereader):
        self.faceGroupCount = filereader.read_uint()
        self.faceGroups = []

        for _ in range(self.faceGroupCount):
            newFaceGroup = RSMAPFaceGroup()
            newFaceGroup.read_face_group(filereader)
            self.faceGroups.append(newFaceGroup)


class RSMAPFaceGroup(object):
    def __init__(self):
        super(RSMAPFaceGroup, self).__init__()

    def __repr__(self):
        #a toggle for verbose information or not
        if False:
            return pprint.pformat(vars(self), indent=1, width=80, depth=2)
        else:
            return super(RSMAPFaceGroup, self).__repr__()

    def read_face_group(self, filereader):
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
        self.vertexParams.read_params(filereader)

        from pprint import pprint
        pprint(self.__dict__)

class RSMAPVertexParameterCollection(object):
    def __init__(self):
        super(RSMAPVertexParameterCollection, self).__init__()
        self.normal = None
        self.UV = None
        self.color = None
    
    def __repr__(self):
        #a toggle for verbose information or not
        if False:
            return pprint.pformat(vars(self))
        else:
            return super(RSMAPVertexParameterCollection, self).__repr__()

    def read_params(self, filereader):
        self.vertexCount = filereader.read_uint()
        print("Number of vertex params: " + str(self.vertexCount))

        self.normals = []
        for _ in range(self.vertexCount):
            self.normals.append(filereader.read_vec_f(3))

        self.UVs = []
        for _ in range(self.vertexCount):
            self.UVs.append(filereader.read_vec_f(2))
        
        self.colors = []
        for _ in range(self.vertexCount):
            self.colors.append(filereader.read_vec_f(4))