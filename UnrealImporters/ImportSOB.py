import unreal_engine as ue
from unreal_engine.classes import Actor, ProceduralMeshComponent, SceneComponent, FloatProperty, KismetMathLibrary, Material
from unreal_engine import FVector, FVector2D, FColor

from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import R6Constants

ue.log('Initializing SOB File importer')

class RenderableMeshComponent(ProceduralMeshComponent):
    def __init__(self):
        pass
        self.CurrentMeshSectionIndex = 0
    
    def ReceiveBeginPlay(self):
        self.CurrentMeshSectionIndex = 0

    def import_renderable(self, renderable, materials):
        vertexArray = []
        #Repack vertices into array of FVectors, and invert X coordinate
        for vertex in renderable.vertices:
            tempVertex = FVector(vertex[0], vertex[1], vertex[2])
            #tempVertex = tempVertex - FVector(32611.490234, 31651.273438, 32911.394531)
            tempVertex = KismetMathLibrary.RotateAngleAxis(tempVertex, 90.0, FVector(1.0, 0.0, 0.0))
            vertexArray.append(tempVertex)

        normalArray = []
        for normal in renderable.normals:
            tempVertex = FVector(normal[0], normal[1], normal[2])
            tempVertex = KismetMathLibrary.RotateAngleAxis(tempVertex, 90.0, FVector(1.0, 0.0, 0.0))
            normalArray.append(tempVertex)

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

        if renderable.materialIndex != R6Constants.UINT_MAX:
            print(str(renderable.materialIndex) + " of " + str(len(materials)))
            self.SetMaterial(self.CurrentMeshSectionIndex, materials[renderable.materialIndex])

        self.CurrentMeshSectionIndex += 1
        ue.log("Created procedural mesh section")

class RSEResourceLoader(Actor):
    def __init__(self):
        pass

    def ReceiveBeginPlay(self):
        pass

class SOBModel(Actor):

    # constructor adding a component
    def __init__(self):
        self.generatedMaterials = []
        self.materialDefinitions = []
        #self.defaultSceneComponent = self.add_actor_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponent = self.add_actor_component(RenderableMeshComponent, 'ProceduralMesh')

    def LoadMaterials(self):
        ue.log("Loading materials: " + str(len(self.materialDefinitions)))
        #Material'/Game/Rainbow/ShermanRommelOpaque.ShermanRommelOpaque'
        parent_material = ue.load_object(Material, '/Game/Rainbow/ShermanRommelOpaque.ShermanRommelOpaque')
        for matDef in self.materialDefinitions:
            mid = self.create_material_instance_dynamic(parent_material)
            if matDef.textureName == "NULL":
                mid.set_material_scalar_parameter('UseVertexColor', 1.0)
            self.generatedMaterials.append(mid)

    def LoadModel(self):
        SOBFile = SOBModelReader.SOBModelFile()
        SOBFile.read_file("D:/R6Data/TestData/ReducedGames/R6GOG/data/model/cessna.sob")
        numGeoObjects = len(SOBFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        ue.log("material definitions: " + str(len(SOBFile.materials)))
        self.materialDefinitions = SOBFile.materials
        self.LoadMaterials()

        renderables = []

        for geoObj in SOBFile.geometryObjects:
            for sourceMesh in geoObj.meshes:
                renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)
        
                for i, currentRenderable in enumerate(renderables):
                    self.proceduralMeshComponent.import_renderable(currentRenderable, materials=self.generatedMaterials)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        self.LoadModel()
        pass

class MAPLevel(RSEResourceLoader):
    # constructor adding a component
    def __init__(self):
        #self.defaultSceneComponent = self.add_actor_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponent = self.add_actor_component(RenderableMeshComponent, 'ProceduralMesh')

    def LoadMap(self):
        MAPFile = MAPLevelReader.MAPLevelFile()
        MAPFile.read_file("D:/R6Data/TestData/ReducedGames/R6GOG/data/map/m01/M01.map")
        numGeoObjects = len(MAPFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        #self.LoadMaterials(MAPFile.materials)

        renderables = []

        for geoObj in MAPFile.geometryObjects:
            for sourceMesh in geoObj.meshes:
                renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)
        
                for i, currentRenderable in enumerate(renderables):
                    self.proceduralMeshComponent.import_renderable(currentRenderable, self.generatedMaterials)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        self.LoadMap()
        pass