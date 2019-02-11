"""This moduled defines classes and functions related to importing RSE assets into Unreal"""
import os
import PIL
from PIL import Image

import unreal_engine as ue
from unreal_engine.classes import Actor, ProceduralMeshComponent, KismetMathLibrary, MaterialInterface, Texture2D
from unreal_engine import FVector, FVector2D, FColor
from unreal_engine.enums import EPixelFormat, TextureAddress

from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import RSBImageReader
from RainbowFileReaders import R6Constants
from RainbowFileReaders import R6Settings
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition
from RainbowFileReaders.R6Constants import RSEAlphaMethod

ue.log('Initializing SOB File importer')

class RenderableMeshComponent(ProceduralMeshComponent):
    """A ProceduralMeshComponent with the ability to convert RenderableArray geometry"""
    def __init__(self):
        self.CurrentMeshSectionIndex = 0

    def ReceiveBeginPlay(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        self.CurrentMeshSectionIndex = 0

    def import_renderable(self, renderable, materials):
        """Adds the specified renderable as a mesh section to this procedural mesh component"""
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
            self.SetMaterial(self.CurrentMeshSectionIndex, materials[renderable.materialIndex])

        self.CurrentMeshSectionIndex += 1

class RSEResourceLoader(Actor):
    """A base class for RSE data formats which provides common functionality"""
    def __init__(self):
        self.generatedMaterials = []
        self.loadedParentMaterials = {}
        self.materialDefinitions = []
        self.loadedTextures = {}

    def ReceiveBeginPlay(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        pass

    def LoadTexture(self, texturePath: str, colorKeyR: int, colorKeyG: int, colorKeyB: int, textureAddressMode: int) -> (Texture2D):
        """Attempts to load the texture at the specified path."""
        if texturePath in self.loadedTextures:
            return self.loadedTextures[texturePath]

        image = None

        # Attempt to load PNG version which will be quicker
        PNGFilename = texturePath.replace(".RSB", ".PNG")
        imageFile = None
        bUsePNGCache = True
        if os.path.isfile(PNGFilename) and bUsePNGCache:
            image = PIL.Image.open(PNGFilename)
        else:
            imageFile = RSBImageReader.RSBImageFile()
            imageFile.read_file(texturePath)
            colokeyMask = (colorKeyR, colorKeyG, colorKeyB)
            image = imageFile.convert_full_color_image_with_colorkey_mask(colokeyMask)
            #Save this image as it will be quicker to load in future
            image.save(PNGFilename, "PNG")

        imageWidth, imageHeight = image.size

        #TODO: generate mip maps
        newTexture = ue.create_transient_texture(imageWidth, imageHeight, EPixelFormat.PF_R8G8B8A8)
        newTexture.texture_set_data(image.tobytes())

        # #These don't appear used in Rainbow Six, but probably will be in Rogue Spear
        # if textureAddressMode == 1: #WRAP
        #     newTexture.AddressX = TextureAddress.TA_Wrap
        #     newTexture.AddressY = TextureAddress.TA_Wrap
        #     newTexture.AddressX = TextureAddress.TA_Clamp
        #     newTexture.AddressY = TextureAddress.TA_Clamp
        # elif textureAddressMode == 3: #CLAMP
        #     newTexture.AddressX = TextureAddress.TA_Clamp
        #     newTexture.AddressY = TextureAddress.TA_Clamp
        #     newTexture.AddressX = TextureAddress.TA_Wrap
        #     newTexture.AddressY = TextureAddress.TA_Wrap
        # else:
        #     ue.log("WARNING: Unknown texture tiling method")

        self.loadedTextures[texturePath] = newTexture
        return newTexture

    def determine_parent_material_required(self, materialDefinition: RSEMaterialDefinition) -> (str):
        """Assesses the material definition and determines the correct parent material to use"""
        #TODO: Determine the correct material variant to load: opaque, masked, translucent and the two sided variants of all
        bTwoSided = False
        if materialDefinition.twoSided:
            bTwoSided = True

        blendMode = "opaque"
        cxpProps = materialDefinition.CXPMaterialProperties
        if cxpProps is not None:
            if cxpProps.blendMode == "alphablend":
                blendMode = "alpha"
            if cxpProps.blendMode == "colorkey":
                if materialDefinition.opacity < 0.99:
                    blendMode = "alpha"
                else:
                    blendMode = "masked"

        materialRequired = "ShermanRommel_" + blendMode
        if bTwoSided:
            materialRequired += "_twosided"

        return materialRequired

    def get_material(self, material_name: str) -> (MaterialInterface):
        if material_name in self.loadedParentMaterials:
            return self.loadedParentMaterials[material_name]

        materialFullPath = "/Game/Rainbow/MasterMaterials/{}.{}".format(material_name, material_name)
        loadedMaterial = None
        try:
            loadedMaterial = ue.load_object(MaterialInterface, materialFullPath)
        except:
            pass
        self.loadedParentMaterials[material_name] = loadedMaterial
        return loadedMaterial

    def LoadMaterials(self):
        """Creates Unreal Material Instances for each material definition"""
        self.texturePaths = R6Settings.get_relevant_global_texture_paths(self.filepath)
        for path in self.texturePaths:
            ue.log("Using Texture Path: " + path)

        verbose = False
        for matDef in self.materialDefinitions:
            parentMaterialName = self.determine_parent_material_required(matDef)
            parentMaterial = self.get_material(parentMaterialName)
            if verbose:
                ue.log("=====================")
                ue.log(matDef.textureName)
                ue.log(parentMaterialName)
            if parentMaterial is None:
                ue.log("Error, could not load parent material: {}".format(parentMaterialName))
                self.generatedMaterials.append(None)
                continue
            mid = self.create_material_instance_dynamic(parentMaterial)

            mid.set_material_scalar_parameter("EmissiveStrength", matDef.emissiveStrength)
            mid.set_material_scalar_parameter("SpecularLevel", matDef.specularLevel)
            mid.set_material_scalar_parameter("Opacity", matDef.opacity)

            colorKeyRGB = None

            if matDef.CXPMaterialProperties is not None:
                if matDef.CXPMaterialProperties.blendMode == "colorkey":
                    cxpProps = matDef.CXPMaterialProperties
                    colorKeyRGB = cxpProps.colorkey

            if colorKeyRGB is None:
                # set this to out of range values, so no special case handling is needed elsewhere as the comparison will always fail, and work will be skipped
                colorKeyRGB = [300, 300, 300]

            #Determine, load and Set diffuse texture
            if matDef.textureName == "NULL":
                mid.set_material_scalar_parameter('UseVertexColor', 1.0)
            else:
                mid.set_material_scalar_parameter('UseVertexColor', 0.0)
                texturesToLoad = []
                texturesToLoad.append(matDef.textureName)
                #Gather all texture names
                if matDef.CXPMaterialProperties is not None:
                    for additionalTexture in matDef.CXPMaterialProperties.animAdditionalTextures:
                        texturesToLoad.append(additionalTexture)
                #Load all textures
                LastTexture = None
                for i, currentTextureName in enumerate(texturesToLoad):
                    foundTexture = None
                    for path in self.texturePaths:
                        foundTexture = R6Settings.find_texture(currentTextureName, path)
                        if foundTexture is not None:
                            break
                    if foundTexture is not None:
                        #This assumes all textures in a flipbook use the same colorkey
                        LastTexture = self.LoadTexture(foundTexture, colorKeyRGB[0], colorKeyRGB[1], colorKeyRGB[2], matDef.textureAddressMode)
                        if LastTexture is not None:
                            currentTextureSlotName = "DiffuseTexture" + str(i)
                            #Add texture to appropriate slot
                            mid.set_material_texture_parameter(currentTextureSlotName,LastTexture)

                #Setup animation properties
                if matDef.CXPMaterialProperties is not None:
                    if matDef.CXPMaterialProperties.animated:
                        mid.set_material_scalar_parameter("AnimationInterval", matDef.CXPMaterialProperties.animInterval)
                        numFrames = len(texturesToLoad)
                        ue.log("Textures to load: " + str(numFrames))
                        mid.set_material_scalar_parameter("NumberOfAnimationFrames", numFrames)
                    else:
                        mid.set_material_scalar_parameter("AnimationInterval", 0.1)
                        mid.set_material_scalar_parameter("NumberOfAnimationFrames", 1)

                    if matDef.CXPMaterialProperties.scrolling:
                        mid.set_material_scalar_parameter("ScrollSpeedX", matDef.CXPMaterialProperties.scrollParams[1])
                        mid.set_material_scalar_parameter("ScrollSpeedY", matDef.CXPMaterialProperties.scrollParams[2])

            self.generatedMaterials.append(mid)

class SOBModel(RSEResourceLoader):
    """Loads an RSE SOB file into unreal assets"""
    # constructor adding a component
    def __init__(self):
        #self.defaultSceneComponent = self.add_actor_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponent = self.add_actor_component(RenderableMeshComponent, 'ProceduralMesh')

    def LoadModel(self):
        """Loads the file and creates appropriate assets in unreal"""
        self.filepath = "D:/R6Data/TestData/ReducedGames/R6GOG/data/model/cessna.sob"
        SOBFile = SOBModelReader.SOBModelFile()
        SOBFile.read_file(self.filepath)
        numGeoObjects = len(SOBFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        ue.log("material definitions: " + str(len(SOBFile.materials)))
        self.materialDefinitions = SOBFile.materials
        self.LoadMaterials()

        renderables = []

        for geoObj in SOBFile.geometryObjects:
            for sourceMesh in geoObj.meshes:
                renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)

                for _, currentRenderable in enumerate(renderables):
                    self.proceduralMeshComponent.import_renderable(currentRenderable, self.generatedMaterials)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        self.LoadModel()

class MAPLevel(RSEResourceLoader):
    """Loads an RSE MAP file into unreal assets"""
    # constructor adding a component
    def __init__(self):
        #self.defaultSceneComponent = self.add_actor_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponent = self.add_actor_component(RenderableMeshComponent, 'ProceduralMesh')

    def LoadMap(self):
        """Loads the file and creates appropriate assets in unreal"""
        self.filepath = "D:/R6Data/TestData/ReducedGames/R6GOG/data/map/m01/M01.map"
        #self.filepath = "D:/R6Data/TestData/ReducedGames/R6GOG/data/map/m02/mansion.map"
        #self.filepath = "D:/R6Data/TestData/ReducedGames/R6GOG/data/map/m09/M09.map"
        MAPFile = MAPLevelReader.MAPLevelFile()
        MAPFile.read_file(self.filepath)
        numGeoObjects = len(MAPFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        ue.log("material definitions: " + str(len(MAPFile.materials)))
        self.materialDefinitions = MAPFile.materials
        self.LoadMaterials()

        renderables = []

        for geoObj in MAPFile.geometryObjects:
            for sourceMesh in geoObj.meshes:
                renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)

                for _, currentRenderable in enumerate(renderables):
                    self.proceduralMeshComponent.import_renderable(currentRenderable, self.generatedMaterials)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        self.LoadMap()
