from RainbowFileReaders import BinaryConversionUtilities
from RainbowFileReaders.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import RSEMaterialFormatConstants, RSEGameVersions
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader

import pprint

#decided to not use Enum for python2.7 compatibility
class SOBAlphaMethod(object):
    SAM_Solid       = 1
    SAM_Masked      = 2 # A guess
    SAM_AlphaBlend  = 3

class SOBModelFile(FileFormatReader):
    """Class to read full SOB files"""
    def __init__(self):
        super(SOBModelFile, self).__init__()
        self.header = None
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []
        self.footer = None

    def read_data(self):
        super().read_data()

        fileReader = self._filereader

        self.header = SOBHeader()
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
                newMaterial.print_structure_info()

        self.geometryListHeader = RSEGeometryListHeader()
        self.geometryListHeader.read(fileReader)
        if self.verboseOutput:
            self.geometryListHeader.print_structure_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            newObj = SOBGeometryObject()
            newObj.read(fileReader)
            self.geometryObjects.append(newObj)
            if self.verboseOutput:
                pass
                #newObj.print_structure_info()

        self.footer = SOBFooterDefinition()
        self.footer.read(fileReader)


class SOBHeader(BinaryFileDataStructure):
    def __init__(self):
        super(SOBHeader, self).__init__()
        self.headerLength = 0
        self.headerBeginMessage = None

    def read(self, filereader):
        super().read(filereader)

        self.headerLength = filereader.read_uint()
        self.headerBeginMessage = filereader.read_bytes(self.headerLength)

class RSEGeometryListHeader(BinaryFileDataStructure):
    def __init__(self):
        super(RSEGeometryListHeader, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.geometryListSize = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.geometryListStringLength = filereader.read_uint()
        self.geometryListStringRaw = filereader.read_bytes(self.geometryListStringLength)
        self.count = filereader.read_uint()

        self.geometryListString = self.geometryListStringRaw[:-1].decode("utf-8")

class SOBGeometryObject(BinaryFileDataStructure):
    def __init__(self):
        super(SOBGeometryObject, self).__init__()
        self.size = None
        self.ID = None
        self.versionStringLength = None
        self.versionNumber = None
        self.versionString = None
        self.objectNameLength = None
        self.objectNameRaw = None
        self.objectName = None
        self.unknown4 = None
        self.unknown5 = None
        self.vertexCount = None
        self.vertices = None
        self.vertexParamsCount = None
        self.vertexParams = None
        self.faceCount = None
        self.faces = None
        self.meshCount = None
        self.meshes = None

    def read(self, filereader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_vertices(filereader)
        self.read_vertex_params(filereader)
        self.read_faces(filereader)
        self.read_meshes(filereader)

    def read_header_info(self, filereader):
        self.size = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.versionStringLength = filereader.read_uint()
        self.versionNumber = None
        if self.versionStringLength == 8:
            self.versionStringRaw = filereader.read_bytes(self.versionStringLength)
            #If the version string was actually set to version, then a version number is stored, along with object name
            if self.versionStringRaw[:-1] == b'Version':
                self.versionNumber = filereader.read_uint()
                self.objectNameLength = filereader.read_uint()
                self.objectNameRaw = filereader.read_bytes(self.objectNameLength)
            self.unknown4 = filereader.read_uint()
            self.unknown5 = filereader.read_uint()
        else:
            self.versionStringRaw = filereader.read_bytes(self.versionStringLength)
        #If an object name was not read, then the version string is actually the name
        if self.objectNameRaw is None: # differs from spec in AlexKimovs repo
            self.objectNameLength = self.versionStringLength
            self.objectNameRaw = self.versionStringRaw
        
        self.objectName = self.objectNameRaw[:-1].decode("utf-8")

    def read_vertices(self, filereader):
        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

    def read_vertex_params(self, filereader):
        self.vertexParamsCount = filereader.read_uint()
        self.vertexParams = []
        for _ in range(self.vertexParamsCount):
            newParams = SOBVertexParameterCollection()
            newParams.read(filereader)
            self.vertexParams.append(newParams)

    def read_faces(self, filereader):
        self.faceCount = filereader.read_uint()
        self.faces = []
        for _ in range(self.faceCount):
            newFace = SOBFaceDefinition()
            newFace.read(filereader)
            self.faces.append(newFace)

    def read_meshes(self, filereader):
        self.meshCount = filereader.read_uint()
        self.meshes = []
        for _ in range(self.meshCount):
            newMesh = SOBMeshDefinition()
            newMesh.read(filereader)
            self.meshes.append(newMesh)

class SOBVertexParameterCollection(BinaryFileDataStructure):
    def __init__(self):
        super(SOBVertexParameterCollection, self).__init__()
        self.normal = None
        self.UV = None
        self.color = None

    def read(self, filereader):
        super().read(filereader)

        self.normal = filereader.read_vec_f(3)
        self.UV = filereader.read_vec_f(2)
        self.unknown10 = filereader.read_float() # no idea?
        self.color = filereader.read_rgb_color_24bpp_uint()

class SOBFaceDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(SOBFaceDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.vertexIndices = filereader.read_vec_uint(3)
        self.paramIndices = filereader.read_vec_uint(3)
        self.faceNormal = filereader.read_vec_f(4)
        self.materialIndex = filereader.read_uint()

#TODO: Check if this is actually smoothing groups
class SOBMeshDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(SOBMeshDefinition, self).__init__()
        self.unknown6 = 0

        self.meshNameLength = 0
        self.meshName = None
        self.meshNameRaw = None

        self.numVertexIndices = 0
        self.vertexIndices = []

        self.numFaceIndices = 0
        self.faceIndices = []

        self.unknown7 = 0

        self.unknown8Length = 0
        self.unknown8Raw = []

        self.unknown9 = 0

    def read(self, filereader):
        super().read(filereader)

        self.unknown6 = filereader.read_uint()

        #read header
        self.meshNameLength = filereader.read_uint()
        self.meshNameRaw = filereader.read_bytes(self.meshNameLength)
        self.meshName = self.meshNameRaw[:-1].decode("utf-8")

        #read vertices
        self.numVertexIndices = filereader.read_uint()
        self.vertexIndices = filereader.read_vec_uint(self.numVertexIndices)

        #read faces
        self.numFaceIndices = filereader.read_uint()
        self.faceIndices = filereader.read_vec_uint(self.numFaceIndices)

        #read unknown7
        self.unknown7 = filereader.read_uint()

        #read unknown8
        self.unknown8Length = filereader.read_uint()
        self.unknown8Raw = filereader.read_bytes(self.unknown8Length)

        #read unknown9
        self.unknown9 = filereader.read_uint()


class SOBFooterDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(SOBFooterDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.EndModelLength = filereader.read_uint()
        self.EndModelString = filereader.read_bytes(self.EndModelLength)

if __name__ == "__main__":
    test = SOBModelFile()
