import unreal_engine as ue
from unreal_engine.classes import Actor, ProceduralMeshComponent, SceneComponent, FloatProperty
from unreal_engine import FVector, FVector2D, FColor

from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import MAPLevelReader

ue.log('Initializing SOB File importer')

class RenderableMeshComponent(ProceduralMeshComponent):
    def __init__(self):
        pass
        self.CurrentMeshSectionIndex = 0
    
    def ReceiveBeginPlay(self):
        self.CurrentMeshSectionIndex = 0

    def import_renderable(self, renderable):
        vertexArray = []
        #Repack vertices into array of FVectors, and invert X coordinate
        for vertex in renderable.vertices:
            vertexArray.append(FVector(vertex[0], vertex[1], vertex[2]))

        normalArray = []
        for normal in renderable.normals:
            normalArray.append(FVector(normal[0], normal[1], normal[2]))

        uvArray = []
        for UV in renderable.UVs:
            uvArray.append(FVector2D(UV[0], UV[1]))

        colorArray = []
        for color in renderable.vertexColors:
            newColor = []
            for element in color:
                newColor.append(int(element * 255))
            colorArray.append(FColor(newColor[0], newColor[1], newColor[2]))

        indexArray = []
        #Repack face vertex indices into flat array
        for face in renderable.triangleIndices:
            indexArray.append(face[2])
            indexArray.append(face[1])
            indexArray.append(face[0])
        
        self.CreateMeshSection(self.CurrentMeshSectionIndex, vertexArray, indexArray, normalArray, UV0=uvArray, VertexColors=colorArray, CreateCollision=True)
        self.CurrentMeshSectionIndex += 1
        ue.log("Created procedural mesh section")

class SOBModel(Actor):

    # constructor adding a component
    def __init__(self):
        #self.defaultSceneComponent = self.add_actor_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponent = self.add_actor_component(RenderableMeshComponent, 'ProceduralMesh')

    def LoadModel(self):
        SOBFile = SOBModelReader.SOBModelFile()
        SOBFile.read_file("D:/R6Data/TestData/ReducedGames/R6GOG/data/model/cessna.sob")
        numGeoObjects = len(SOBFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        renderables = []

        for geoObj in SOBFile.geometryObjects:
            for sourceMesh in geoObj.meshes:
                renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)
        
                for i, currentRenderable in enumerate(renderables):
                    self.proceduralMeshComponent.import_renderable(currentRenderable)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        self.LoadModel()
        pass
    
    # this will automatically override the OnSeePawn event
    def OnSeePawn(self, pawn : Pawn):
        ue.print_string('seen {}'.format(pawn))

class MAPLevel(Actor):
    # constructor adding a component
    def __init__(self):
        #self.defaultSceneComponent = self.add_actor_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponent = self.add_actor_component(RenderableMeshComponent, 'ProceduralMesh')

    def LoadMap(self):
        MAPFile = MAPLevelReader.MAPLevelFile()
        MAPFile.read_file("D:/R6Data/TestData/ReducedGames/R6GOG/data/map/m01/M01.map")
        numGeoObjects = len(MAPFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        renderables = []

        for geoObj in MAPFile.geometryObjects:
            for sourceMesh in geoObj.meshes:
                renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)
        
                for i, currentRenderable in enumerate(renderables):
                    self.proceduralMeshComponent.import_renderable(currentRenderable)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        self.LoadMap()
        pass