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
                #newObj.print_object_info()
        
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

        self.geometryObjectHeader = RSMAPGeometryObjectHeader()
        self.geometryObjectHeader.read_header(filereader)


        pass


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
        print(str(self.nameStringRaw))
        self.nameString = self.nameStringRaw[:-1].decode("utf-8")

        self.read_vertices(filereader)

        self.read_faces(filereader)

        print("==================================")

    def read_vertices(self, filereader):
        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

        print(str(len(self.vertices)))

    def read_faces(self, filereader):
        self.faceCount = filereader.read_uint()
        #self.faces = []
        self.faceNormals = []
        self.faceDistances = []
        for _ in range(self.faceCount):
            #newFace = RSMAPFaceDefinition()
            #newFace.read_face(filereader)
            newFaceNormal = filereader.read_vec_f(3)
            self.faceNormals.append(newFaceNormal)

            newFaceDistance = filereader.read_float()
            self.faceDistances.append(newFaceDistance)
        
        self.faceVertexIndices = []
        for _ in range(self.faceCount):
            #hardcoded to 3 vertices per face
            newFaceVertIndices = filereader.read_vec_short_uint(3)
            self.faceVertexIndices.append(newFaceVertIndices)

        self.faceParamIndices = []
        for _ in range(self.faceCount):
            #hardcoded to 3 vertices per face
            newFaceParamIndices = filereader.read_vec_short_uint(3)
            self.faceParamIndices.append(newFaceParamIndices)

        self.vertexParamsCount = filereader.read_uint()
        self.vertexParams = []
        for _ in range(self.vertexParamsCount):
            pass


class R(object):
    def __init__(self):
        super(RSMAPFaceDefinition, self).__init__()

    def __repr__(self):
        #a toggle for verbose information or not
        if False:
            return pprint.pformat(vars(self), indent=1, width=80, depth=2)
        else:
            return super(RSMAPFaceDefinition, self).__repr__()

    def read_face(self, filereader):
        self.vertexIndices = filereader.read_vec_uint(3)
        self.paramIndices = filereader.read_vec_uint(3)
        self.faceNormal = filereader.read_vec_f(4)
        self.materialIndex = filereader.read_uint()