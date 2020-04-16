"""Defines common geometry data structures used in many Red Storm Entertainment file formats"""

from typing import List, Tuple, Dict

from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, SizedCString, BinaryFileReader
from RainbowFileReaders.R6Constants import RSEGeometryFlags
from RainbowFileReaders.MathHelpers import normalize_color, pad_color, IntIterable
from RainbowFileReaders.RenderableArray import RenderableArray

class RSEGeometryListHeader(BinaryFileDataStructure):
    """Stores the information about a Geometry List"""
    def __init__(self):
        super(RSEGeometryListHeader, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.geometryListSize: int = filereader.read_uint32()
        self.id: int = filereader.read_uint32()
        self.geometry_list_string: SizedCString = SizedCString(filereader)
        self.count: int = filereader.read_uint32()

class R6GeometryObject(BinaryFileDataStructure):
    """Reads and stores a Rainbow Six Geometry Object"""
    def __init__(self):
        super(R6GeometryObject, self).__init__()
        self.size: int = None
        self.id: int = None
        self.name_string: SizedCString = None
        self.version_string: SizedCString = None
        self.versionNumber: int = None
        self.unknown4: int = None
        self.unknown5: int = None
        self.vertexCount: int = None
        self.vertices: List[List[float]] = []
        self.vertexParamsCount: int = None
        self.vertexParams: List[R6VertexParameterCollection] = None
        self.faceCount: int = None
        self.faces: List[R6FaceDefinition] = None
        self.meshCount: int = None
        self.meshes: List[R6MeshDefinition] = None

    def generate_renderable_arrays_for_mesh(self, mesh: R6MeshDefinition) -> List[RenderableArray]:
        """ Generates a list of RenderableArray objects from the internal data structure """
        renderables: List[RenderableArray] = []
        uniqueMaterials = set()
        for faceIdx in mesh.faceIndices:
            currentFace = self.faces[faceIdx]
            uniqueMaterials.add(currentFace.materialIndex)

        for materialIdx in uniqueMaterials:
            attribList: List[Tuple[int, int]] = []
            triangleIndices: List[IntIterable] = []

            #build list of sets of vertices and associated params, and list of new triangle indices
            for faceIdx in mesh.faceIndices:
                currentFace = self.faces[faceIdx]
                if currentFace.materialIndex == materialIdx:
                    # Add this face to the current renderable
                    currentTriangleIndices = []
                    for vertIndex in range(len(currentFace.vertexIndices)):
                        #Build a list of attributes paired with a vertex, which we can use to reduce total array length in the RenderableArray
                        currentAttribs = (currentFace.vertexIndices[vertIndex], currentFace.paramIndices[vertIndex])
                        if currentAttribs in attribList:
                            currentTriangleIndices.append(attribList.index(currentAttribs))
                        else:
                            attribList.append(currentAttribs)
                            currentTriangleIndices.append(attribList.index(currentAttribs))
                    triangleIndices.append(currentTriangleIndices)

            currentRenderable = RenderableArray()
            currentRenderable.normals = []
            currentRenderable.UVs = []
            currentRenderable.vertexColors = []
            # fill out new renderable by unravelling and expanding the vertex and param pairs
            for currentAttribSet in attribList:
                # Make sure to copy any arrays so any transforms don't get interferred with in other renderables
                currentVertex = self.vertices[currentAttribSet[0]]
                currentVertexParams = self.vertexParams[currentAttribSet[1]]
                currentRenderable.vertices.append(currentVertex.copy())
                currentRenderable.normals.append(currentVertexParams.normal.copy())
                currentRenderable.UVs.append(currentVertexParams.UV.copy())

                # Convert color to RenderableArray standard format, RGBA 0.0-1.0 range
                importedColorCopy = currentVertexParams.color.copy()
                # convert the color to 0.0-1.0 range, rather than 0-255
                importedColor = normalize_color(importedColorCopy)
                # pad with an alpha value so it's RGBA
                importedColor = pad_color(importedColor)
                currentRenderable.vertexColors.append(importedColor)
            # Assign the specified material
            currentRenderable.materialIndex = materialIdx
            # set the triangle indices
            currentRenderable.triangleIndices = triangleIndices

            renderables.append(currentRenderable)

        return renderables

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.read_header_info(filereader)
        self.read_vertices(filereader)
        self.read_vertex_params(filereader)
        self.read_faces(filereader)
        self.read_meshes(filereader)

    def read_header_info(self, filereader: BinaryFileReader):
        """Reads top level information for this data structure"""
        self.size = filereader.read_uint32()
        self.ID = filereader.read_uint32()
        self.name_string = SizedCString(filereader)
        #If the version string was actually set to version, then a version number is stored, along with object name
        if self.name_string.string == 'Version':
            self.version_string = self.name_string
            self.versionNumber = filereader.read_uint32()
            self.name_string = SizedCString(filereader)
            self.unknown4 = filereader.read_uint32()
            self.unknown5 = filereader.read_uint32()

    def read_vertices(self, filereader: BinaryFileReader):
        """ Reads a count of the number of vertices, followed by the list of vertices """
        self.vertexCount = filereader.read_uint32()
        self.vertices = []
        for _ in range(self.vertexCount):
            self.vertices.append(filereader.read_vec_f(3))

    def read_vertex_params(self, filereader: BinaryFileReader):
        """ Reads a count of the number of vertex parameters, followed by the list of vertex parameters """
        self.vertexParamsCount = filereader.read_uint32()
        self.vertexParams = []
        for _ in range(self.vertexParamsCount):
            newParams = R6VertexParameterCollection()
            newParams.read(filereader)
            self.vertexParams.append(newParams)

    def read_faces(self, filereader: BinaryFileReader):
        """ Reads a count of the number of faces, followed by the list of faces """
        self.faceCount = filereader.read_uint32()
        self.faces = []
        for _ in range(self.faceCount):
            newFace = R6FaceDefinition()
            newFace.read(filereader)
            self.faces.append(newFace)

    def read_meshes(self, filereader: BinaryFileReader):
        """ Reads a count of the number of meshes, followed by the list of meshes """
        self.meshCount = filereader.read_uint32()
        self.meshes = []
        for _ in range(self.meshCount):
            newMesh = R6MeshDefinition()
            newMesh.read(filereader)
            self.meshes.append(newMesh)

class R6VertexParameterCollection(BinaryFileDataStructure):
    """ Contains a given pair/set of attributes for a particular vertex. Contains, normal, UV and color values """
    def __init__(self):
        super(R6VertexParameterCollection, self).__init__()
        self.normal: List[float] = None
        self.UV: List[float] = None
        self.unknown10: float = None
        self.color: List[int] = None

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.normal = filereader.read_vec_f(3)
        self.UV = filereader.read_vec_f(2)
        self.unknown10 = filereader.read_float() # no idea?
        self.color = filereader.read_rgb_color_24bpp_uint()

class R6FaceDefinition(BinaryFileDataStructure):
    """ Contains a list of properties for an individual face. Contains indices for the vertices and parameters, as well as the face normal and material assigned """
    def __init__(self):
        super(R6FaceDefinition, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.vertexIndices: List[int] = filereader.read_vec_uint32(3)
        self.paramIndices: List[int] = filereader.read_vec_uint32(3)
        self.faceNormal: List[float] = filereader.read_vec_f(4)
        self.materialIndex: int = filereader.read_uint32()

class R6MeshDefinition(BinaryFileDataStructure):
    """ Contains a list of faces that make up this mesh, as well as some associated properties """
    def __init__(self):
        super(R6MeshDefinition, self).__init__()
        self.unknown6: int = 0

        self.name_string: SizedCString = SizedCString()

        self.numVertexIndices: int = 0
        self.vertexIndices: List[int] = []

        self.numFaceIndices: int = 0
        self.faceIndices: List[int] = []

        self.geometryFlags: int = 0
        self.geometryFlagsEvaluated: Dict[str, bool] = {}

        self.unknown_8_string: SizedCString = SizedCString()

        self.unknown9: int = 0

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.unknown6 = filereader.read_uint32()

        #read header
        self.name_string = SizedCString(filereader)

        #read vertices
        self.numVertexIndices = filereader.read_uint32()
        self.vertexIndices = filereader.read_vec_uint32(self.numVertexIndices)

        #read faces
        self.numFaceIndices = filereader.read_uint32()
        self.faceIndices = filereader.read_vec_uint32(self.numFaceIndices)

        #read geometryFlags
        self.geometryFlags = filereader.read_uint32()
        self.geometryFlagsEvaluated = RSEGeometryFlags.EvaluateFlags(self.geometryFlags)

        #read unknown8
        self.unknown_8_string = SizedCString(filereader)

        #read unknown9
        self.unknown9 = filereader.read_uint32()
