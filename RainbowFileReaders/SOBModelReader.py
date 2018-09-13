from RainbowFileReaders import BinaryConversionUtilities
import pprint

class SOBModelFile(object):
    """Class to read full SOB files"""
    def __init__(self):
        super(SOBModelFile, self).__init__()
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []

    def read_sob(self, filename):
        modelFile = BinaryConversionUtilities.BinaryFileReader(filename)

        self.header = SOBHeader()
        self.header.read_header(modelFile)
        #self.header.print_header_info()

        self.materialListHeader = SOBMaterialListHeader()
        self.materialListHeader.read_header(modelFile)
        #self.materialListHeader.print_header_info()

        self.materials = []
        for i in range(self.materialListHeader.numMaterials):
            newMaterial = SOBMaterialDefinition()
            newMaterial.read_material(modelFile)
            #newMaterial.print_material_info()
            self.materials.append(newMaterial)

        self.geometryListHeader = SOBGeometryListHeader()
        self.geometryListHeader.read_header(modelFile)
        #self.geometryListHeader.print_header_info()

        self.geometryObjects = []
        for i in range(self.geometryListHeader.count):
            newObj = SOBGeometryObject()
            newObj.read_object(modelFile)
            #newObj.print_object_info()
            self.geometryObjects.append(newObj)
        
        print("Processed: " + str(modelFile.get_seekg()) + " bytes")
        print("Length: " + str(modelFile.get_length()) + " bytes")
        print("Unprocessed: " + str(modelFile.get_length() - modelFile.get_seekg()) + " bytes")


class SOBHeader(object):
    def __init__(self):
        super(SOBHeader, self).__init__()
        self.headerLength = 0
        self.headerBeginMessage = None

    def read_header(self, filereader):
        self.headerLength = filereader.read_uint()
        self.headerBeginMessage = filereader.read_bytes(self.headerLength)

    def print_header_info(self):
        print("Header length: " + str(self.headerLength))
        print("Header message: " + str(self.headerBeginMessage))
        print("")

class SOBMaterialListHeader(object):
    def __init__(self):
        super(SOBMaterialListHeader, self).__init__()
        self.materialListSize = None
        self.unknown1 = None
        self.materialBeginMessageLength = None
        self.materialBeginMessage = None
        self.numMaterials = None

    def read_header(self, filereader):
        self.materialListSize = filereader.read_uint()
        self.unknown1 = filereader.read_uint()
        self.materialBeginMessageLength = filereader.read_uint()
        self.materialBeginMessage = filereader.read_bytes(self.materialBeginMessageLength)
        self.numMaterials = filereader.read_uint()

    def print_header_info(self):
        print("Material list size: " + str(self.materialListSize))
        print("unknown1: " + str(self.unknown1))
        print("Number of materials: " + str(self.numMaterials))
        print("Begin message length: " + str(self.materialBeginMessageLength))
        print("Begin message: " + str(self.materialBeginMessage))
        print("")


class SOBMaterialDefinition(object):
    def __init__(self):
        super(SOBMaterialDefinition, self).__init__()
        self.materialSize = None
        self.ID = None
        self.versionStringLength = None
        self.versionNumber = None
        self.versionString = None
        self.materialNameLength = None
        self.materialName = None
        self.textureNameLength = None
        self.textureName = None
        self.opacity = None
        self.unknown2 = None
        self.unknown3 = None
        self.ambient = None
        self.diffuse = None
        self.specular = None
        self.specularLevel = None
        self.twoSided = None

    def read_material(self, filereader):
        self.materialSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.versionStringLength = filereader.read_uint()
        self.versionNumber = None
        if self.versionStringLength == 8:
            self.versionString = filereader.read_bytes(self.versionStringLength)
            if self.versionString[:-1] == b'Version':
                self.versionNumber = filereader.read_uint()
                self.materialNameLength = filereader.read_uint()
                self.materialName = filereader.read_bytes(self.materialNameLength)
            else:
                self.materialNameLength = self.versionStringLength
                self.materialName = self.versionString
        else:
            self.materialNameLength = self.versionStringLength
            self.materialName = filereader.read_bytes(self.materialNameLength)

        self.textureNameLength = filereader.read_uint()
        self.textureName = filereader.read_bytes(self.textureNameLength)

        self.opacity = filereader.read_float()
        self.unknown2 = filereader.read_float()
        self.unknown3 = filereader.read_uint()
        self.ambient = filereader.read_rgb_color_32bpp_uint()
        self.diffuse = filereader.read_rgb_color_32bpp_uint()
        self.specular = filereader.read_rgb_color_32bpp_uint()
        self.specularLevel = filereader.read_float()
        self.twoSided = filereader.read_bytes(1)


    def print_material_info(self):
        print("Material size: " + str(self.materialSize))
        print("ID: " + str(self.ID))
        print("Material Name Length: " + str(self.materialNameLength))
        print("Material Name: " + str(self.materialName.decode("utf-8")))
        print("Texture Name Length: " + str(self.textureNameLength))
        print("Texture Name: " + str(self.textureName.decode("utf-8")))
        print("")

class SOBGeometryListHeader(object):
    def __init__(self):
        super(SOBGeometryListHeader, self).__init__()

    def read_header(self, filereader):
        self.geometryListSize = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.geometryListStringLength = filereader.read_uint()
        self.geometryListString = filereader.read_bytes(self.geometryListStringLength)
        self.count = filereader.read_uint()

    def print_header_info(self):
        pprint.pprint(vars(self))

class SOBGeometryObject(object):
    def __init__(self):
        super(SOBGeometryObject, self).__init__()
        self.objectSize = None
        self.ID = None
        self.versionStringLength = None
        self.versionNumber = None
        self.versionString = None
        self.objectNameLength = None
        self.objectNameString = None
        self.objectName = None
        self.unknown4 = None
        self.unknown5 = None

    def read_object(self, filereader):
        self.objectSize = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.versionStringLength = filereader.read_uint()
        self.versionNumber = None
        if self.versionStringLength == 8:
            self.versionString = filereader.read_bytes(self.versionStringLength)
            if self.versionString[:-1] == b'Version':
                self.versionNumber = filereader.read_uint()
                self.objectNameLength = filereader.read_uint()
                self.objectNameString = filereader.read_bytes(self.objectNameLength)
            self.unknown4 = filereader.read_uint()
            self.unknown5 = filereader.read_uint()
        else:
            self.versionString = filereader.read_bytes(self.versionStringLength)
        if self.objectNameString is None: # differs from spec in AlexKimovs repo
            print("Warning: This code is untested")
            self.objectNameLength = self.versionStringLength
            self.objectNameString = self.versionString
        
        self.objectName = self.objectNameString[:-1].decode("utf-8")

        self.read_vertices(filereader)
        self.read_vertex_params(filereader)
        self.read_faces(filereader)
        

    def read_vertices(self, filereader):
        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for i in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

    def read_vertex_params(self, filereader):
        self.vertexParamsCount = filereader.read_uint()
        self.vertexParams = []
        for i in range(self.vertexParamsCount):
            newParams = SOBVertexParameterCollection()
            newParams.read_params(filereader)
            self.vertexParams.append(newParams)

    def read_faces(self, filereader):
        self.faceCount = filereader.read_uint()
        self.faces = []
        for i in range(self.faceCount):
            newFace = SOBFaceDefinition()
            newFace.read_face(filereader)
            self.faces.append(newFace)

    def print_object_info(self):
        pprint.pprint(vars(self))

class SOBVertexParameterCollection(object):
    def __init__(self):
        super(SOBVertexParameterCollection, self).__init__()
        self.normal = None
        self.UV = None
        self.color = None
    
    def __repr__(self):
        #a toggle for verbose information or not
        if False:
            return pprint.pformat(vars(self))
        else:
            return super(SOBVertexParameterCollection, self).__repr__()

    def read_params(self, filereader):
        self.normal = filereader.read_vec_f(4)
        self.UV = filereader.read_vec_f(2)
        self.color = filereader.read_rgb_color_32bpp_uint()

class SOBFaceDefinition(object):
    def __init__(self):
        super(SOBFaceDefinition, self).__init__()

    def __repr__(self):
        #a toggle for verbose information or not
        if False:
            return pprint.pformat(vars(self), indent=1, width=80, depth=2)
        else:
            return super(SOBFaceDefinition, self).__repr__()

    def read_face(self, filereader):
        self.vertexIndices = filereader.read_vec_uint(3)
        self.paramIndices = filereader.read_vec_uint(3)
        self.faceNormal = filereader.read_vec_f(4)
        self.materialIndex = filereader.read_uint()

if __name__ == "__main__":
    test = SOBModelFile()
