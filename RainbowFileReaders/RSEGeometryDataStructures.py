from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure
from RainbowFileReaders.R6Constants import RSEGeometryFlags

class RSEGeometryListHeader(BinaryFileDataStructure):
    def __init__(self):
        super(RSEGeometryListHeader, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.geometryListSize = filereader.read_uint()
        self.ID = filereader.read_uint()
        self.read_named_string(filereader, "geometryListString")
        self.count = filereader.read_uint()

class R6GeometryObject(BinaryFileDataStructure):
    def __init__(self):
        super(R6GeometryObject, self).__init__()
        self.size = None
        self.ID = None
        self.versionStringLength = None
        self.versionNumber = None
        self.versionString = None
        self.nameStringLength = None
        self.nameStringRaw = None
        self.nameString = None
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
        self.read_version_string(filereader)
        self.versionNumber = None
        #If the version string was actually set to version, then a version number is stored, along with object name
        if self.versionString == 'Version':
            self.versionNumber = filereader.read_uint()
            self.read_name_string(filereader)
            self.unknown4 = filereader.read_uint()
            self.unknown5 = filereader.read_uint()
        #If an object name was not read, then the version string is actually the name
        if self.nameStringRaw is None: # differs from spec in AlexKimovs repo
            self.nameStringLength = self.versionStringLength
            self.nameStringRaw = self.versionStringRaw
            self.nameString = self.versionString

    def read_vertices(self, filereader):
        self.vertexCount = filereader.read_uint()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

    def read_vertex_params(self, filereader):
        self.vertexParamsCount = filereader.read_uint()
        self.vertexParams = []
        for _ in range(self.vertexParamsCount):
            newParams = R6VertexParameterCollection()
            newParams.read(filereader)
            self.vertexParams.append(newParams)

    def read_faces(self, filereader):
        self.faceCount = filereader.read_uint()
        self.faces = []
        for _ in range(self.faceCount):
            newFace = R6FaceDefinition()
            newFace.read(filereader)
            self.faces.append(newFace)

    def read_meshes(self, filereader):
        self.meshCount = filereader.read_uint()
        self.meshes = []
        for _ in range(self.meshCount):
            newMesh = R6MeshDefinition()
            newMesh.read(filereader)
            self.meshes.append(newMesh)

class R6VertexParameterCollection(BinaryFileDataStructure):
    def __init__(self):
        super(R6VertexParameterCollection, self).__init__()
        self.normal = None
        self.UV = None
        self.color = None

    def read(self, filereader):
        super().read(filereader)

        self.normal = filereader.read_vec_f(3)
        self.UV = filereader.read_vec_f(2)
        self.unknown10 = filereader.read_float() # no idea?
        self.color = filereader.read_rgb_color_24bpp_uint()

class R6FaceDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6FaceDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.vertexIndices = filereader.read_vec_uint(3)
        self.paramIndices = filereader.read_vec_uint(3)
        self.faceNormal = filereader.read_vec_f(4)
        self.materialIndex = filereader.read_uint()

#TODO: Check if this is actually smoothing groups
class R6MeshDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(R6MeshDefinition, self).__init__()
        self.unknown6 = 0

        self.numVertexIndices = 0
        self.vertexIndices = []

        self.numFaceIndices = 0
        self.faceIndices = []

        self.geometryFlags = 0

        self.unknown9 = 0

        self.nameStringLength = 0
        self.nameStringRaw = None
        self.nameString = None

    def read(self, filereader):
        super().read(filereader)

        self.unknown6 = filereader.read_uint()

        #read header
        self.read_name_string(filereader)

        #read vertices
        self.numVertexIndices = filereader.read_uint()
        self.vertexIndices = filereader.read_vec_uint(self.numVertexIndices)

        #read faces
        self.numFaceIndices = filereader.read_uint()
        self.faceIndices = filereader.read_vec_uint(self.numFaceIndices)

        #read geometryFlags
        self.geometryFlags = filereader.read_uint()
        self.geometryFlagsEvaluated = RSEGeometryFlags.EvaluateFlags(self.geometryFlags)

        #read unknown8
        self.read_named_string(filereader, "unknown8String")

        #read unknown9
        self.unknown9 = filereader.read_uint()