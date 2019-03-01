"""This moduled defines classes and functions related to importing RSE assets into Unreal"""
import os
import PIL
from PIL import Image

import unreal_engine as ue
from unreal_engine.classes import Actor, SceneComponent, CustomProceduralMeshComponent, KismetMathLibrary, MaterialInterface, Texture2D, TestActor
from unreal_engine import FVector, FVector2D, FColor, FRotator, FLinearColor
from unreal_engine.enums import EPixelFormat, TextureAddress

from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import RSBImageReader
from RainbowFileReaders import R6Constants
from RainbowFileReaders import R6Settings
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition
from RainbowFileReaders.R6Constants import RSEGameVersions
from RainbowFileReaders.RenderableArray import AxisAlignedBoundingBox, RenderableArray

from UnrealImporters import ImporterSettings

ue.log('Initializing SOB File importer')

class RSEResourceLoader:
    """A base class for RSE data formats which provides common functionality"""
    def __init__(self):
        self.generatedMaterials = []
        self.loadedParentMaterials = {}
        self.materialDefinitions = []
        self.loadedTextures = {}

    def begin_play(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        pass

    def LoadTexture(self, texturePath: str, colorKeyR: int, colorKeyG: int, colorKeyB: int, textureAddressMode: int) -> (Texture2D):
        """Attempts to load the texture at the specified path."""
        if texturePath in self.loadedTextures:
            return self.loadedTextures[texturePath]

        if os.path.isfile(texturePath) is False:
            ue.log("Could not find texture to load: " + texturePath)
            return None
        image = None

        # Attempt to load PNG version which will be quicker
        PNGFilename = texturePath + ImporterSettings.PNG_CACHE_FILE_SUFFIX
        imageFile = None
        if os.path.isfile(PNGFilename) and ImporterSettings.bUsePNGCache:
            image = PIL.Image.open(PNGFilename)
        else:
            imageFile = RSBImageReader.RSBImageFile()
            imageFile.read_file(texturePath)
            colokeyMask = (colorKeyR, colorKeyG, colorKeyB)
            image = imageFile.convert_full_color_image_with_colorkey_mask(colokeyMask)
            if ImporterSettings.bUsePNGCache:
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
            if tuple(cxpProps.textureformat) == (0, 4, 4, 4, 4):
                blendMode = "alpha"

        materialRequired = "ShermanRommel_" + blendMode
        if bTwoSided:
            materialRequired += "_twosided"

        return materialRequired

    def get_unreal_master_material(self, material_name: str) -> (MaterialInterface):
        """Gets an unreal material for use. If it's not already loaded, it will load it automatically and cache it for next time"""
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
            verbose = False
            if matDef.textureName.startswith("cl02_spray1"):
                verbose = True
            parentMaterialName = self.determine_parent_material_required(matDef)
            parentMaterial = self.get_unreal_master_material(parentMaterialName)
            if verbose:
                ue.log("=====================")
                ue.log(matDef.textureName)
                ue.log(parentMaterialName)
            if parentMaterial is None:
                ue.log("Error, could not load parent material: {}".format(parentMaterialName))
                self.generatedMaterials.append(None)
                continue
            mid = self.uobject.create_material_instance_dynamic(parentMaterial)

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
                #Add the first texture
                texturesToLoad.append(matDef.textureName)
                #Gather all other texture names
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
                    else:
                        ue.log("Failed to find texture: " + currentTextureName)

                #Setup animation properties
                if matDef.CXPMaterialProperties is not None:
                    if matDef.CXPMaterialProperties.animated:
                        mid.set_material_scalar_parameter("AnimationInterval", matDef.CXPMaterialProperties.animInterval)
                        numFrames = len(texturesToLoad)
                        ue.log("Number of animation frames: " + str(numFrames))
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
        self.defaultSceneComponent = self.add_actor_root_component(SceneComponent, 'DefaultSceneComponent')
        #self.proceduralMeshComponent = self.add_actor_component(CustomProceduralMeshComponent, 'ProceduralMesh')

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

        # for geoObj in SOBFile.geometryObjects:
        #     for sourceMesh in geoObj.meshes:
        #         renderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)

        #         for _, currentRenderable in enumerate(renderables):
        #             self.proceduralMeshComponent.import_renderable(currentRenderable, self.generatedMaterials)

        ue.log("Created procedural mesh")

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        self.LoadModel()

class MAPLevel(RSEResourceLoader):
    """Loads an RSE MAP file into unreal assets"""
    # constructor adding a component
    def begin_play(self):
        self.defaultSceneComponent = self.uobject.add_actor_root_component(SceneComponent, 'DefaultSceneComponent')
        self.proceduralMeshComponents = []
        # All AABBs for each static geometry object should be added to this worldAABB
        # This will allow an offset to be calculated to shift the map closer to the world origin, buying back precision
        self.worldAABB = AxisAlignedBoundingBox()
        self.shift_origin = True
        self.LoadMap()

    def tick(self, delta_time):
        pass

    def import_lights(self, MAPFile):
        self.uobject.SpawnLightActor()
        light_actor = self.uobject.LightActor

        for lightDef in MAPFile.lightList.lights:
            # Place lamp to a specified location
            position = self.PositionListToFVector(lightDef.position, True)
            if self.shift_origin:
                position = position - self.worldOffsetVec

            color = []
            for color_el in lightDef.color:
                color.append(color_el / 255.0)
            linearColor = FLinearColor(color[0], color[1], color[2])

            constAtten = lightDef.constantAttenuation
            linAtten = lightDef.linearAttenuation
            quadAtten = lightDef.quadraticAttenuation
            energy = lightDef.energy
            falloff = lightDef.falloff
            lightType = lightDef.type
            lightName = lightDef.nameString

            light_actor.AddPointlight(position, linearColor, constAtten, linAtten, quadAtten, falloff, energy, lightType, lightName)

        if MAPFile.dmpLights is not None:
            for lightDef in MAPFile.dmpLights.lights:
                # Place lamp to a specified location
                position = self.PositionListToFVector(lightDef.position, True)
                if self.shift_origin:
                    position = position - self.worldOffsetVec

                color = []
                for color_el in lightDef.diffuseColor:
                    color.append(color_el)
                linearColor = FLinearColor(color[0], color[1], color[2])

                constAtten = lightDef.constantAttenuation
                linAtten = lightDef.linearAttenuation
                quadAtten = lightDef.quadraticAttenuation
                energy = lightDef.energy
                falloff = lightDef.falloff
                lightType = lightDef.type
                lightName = lightDef.nameString

                light_actor.AddPointlight(position, linearColor, constAtten, linAtten, quadAtten, falloff, energy, lightType, lightName)

    def set_geometry_flags(self, mesh_component, collision_only, flags_dict):
        if flags_dict is None:
            return

        if mesh_component is None:
            return

        mesh_component.bCollisionOnly = collision_only
        mesh_component.bHasRSEGeometryFlags = True
        mesh_component.bGF_Climbable = flags_dict["GF_CLIMBABLE"]
        mesh_component.bGF_NoCollide2D = flags_dict["GF_NOCOLLIDE2D"]
        mesh_component.bGF_Invisible = flags_dict["GF_INVISIBLE"]
        mesh_component.bGF_Unknown2 = flags_dict["GF_UNKNOWN2"]
        mesh_component.bGF_FloorPolygon = flags_dict["GF_FLOORPOLYGON"]
        mesh_component.bGF_NoCollide3D = flags_dict["GF_NOCOLLIDE3D"]
        mesh_component.bGF_Unknown4 = flags_dict["GF_UNKNOWN4"]
        mesh_component.bGF_NotShownInPlan = flags_dict["GF_NOTSHOWNINPLAN"]

    def LoadMap(self):
        """Loads the file and creates appropriate assets in unreal"""
        self.filepath = ImporterSettings.map_file_path
        MAPFile = MAPLevelReader.MAPLevelFile()
        MAPFile.read_file(self.filepath)
        numGeoObjects = len(MAPFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        ue.log("material definitions: " + str(len(MAPFile.materials)))
        self.materialDefinitions = MAPFile.materials
        self.LoadMaterials()

        usedNames = []
        self.objectComponents = []

        self.worldOffsetVec = FVector(0, 0, 0)

        for _, geoObj in enumerate(MAPFile.geometryObjects):
            name = geoObj.nameString
            if name in usedNames:
                ue.log("Duplicate name!")
            else:
                usedNames.append(name)

            if MAPFile.gameVersion == RSEGameVersions.RAINBOW_SIX:
                geoObjComponent = self.uobject.add_actor_component(SceneComponent, name, self.defaultSceneComponent)
                self.objectComponents.append(geoObjComponent)
                self.uobject.add_instance_component(geoObjComponent)
                self.uobject.modify()
                for srcMeshIdx, sourceMesh in enumerate(geoObj.meshes):
                    renderableName = name + "_" + sourceMesh.nameString + "_" + str(srcMeshIdx)
                    currRenderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)
                    newMeshComponent = self.import_renderables_as_mesh_component(renderableName, currRenderables, self.shift_origin, geoObjComponent)

                    self.set_geometry_flags(newMeshComponent, False, sourceMesh.geometryFlagsEvaluated)

            else: # Rogue spear
                #Setup all visual geometry
                renderables = []
                for _, facegroup in enumerate(geoObj.geometryData.faceGroups):
                    renderable = geoObj.geometryData.generate_renderable_array_for_facegroup(facegroup)
                    renderables.append(renderable)
                #TODO: Refactor the merging here to take into account surfaces properties, so objects with different collision properties can be separated
                #TODO: Pass through CXP gunpass grenadepass tags to the newly separated geometry
                self.import_renderables_as_mesh_component(name, renderables, self.shift_origin, self.defaultSceneComponent)

                #setup collision geometry
                collisionName = name + "_collision"
                collisionComponent = self.uobject.add_actor_component(SceneComponent, collisionName, self.defaultSceneComponent)
                collisionData = geoObj.geometryData.collisionInformation
                for i, collMesh in enumerate(collisionData.collisionMeshDefinitions):
                    if collMesh.geometryFlagsEvaluated["GF_INVISIBLE"] is True:
                        #Do not process invalid and unused meshes
                        pass
                        #continue
                    subCollisionName = collisionName + "_idx" + str(i)
                    renderable = collisionData.generate_renderable_array_for_collisionmesh(collMesh, geoObj.geometryData)
                    newMeshComponent = self.import_renderables_as_mesh_component(subCollisionName, [renderable], self.shift_origin, collisionComponent)

                    self.set_geometry_flags(newMeshComponent, True, collMesh.geometryFlagsEvaluated)

        if self.shift_origin:
            # Once all meshes have been imported, the WorldAABB will properly encapsulate the entire level,
            # and an appropriate offset can be calculated to bring each object back closer to the origin
            worldOffset = self.worldAABB.get_center_position()
            self.worldOffsetVec = FVector(worldOffset[0], worldOffset[1], worldOffset[2])
            self.worldOffsetVec = KismetMathLibrary.RotateAngleAxis(self.worldOffsetVec, 90.0, FVector(1.0, 0.0, 0.0))
            for currentMesh in self.proceduralMeshComponents:
                # Only shift static elements
                if currentMesh.get_relative_location().length() > 1000.0:
                    newLoc = currentMesh.get_relative_location() - self.worldOffsetVec
                    currentMesh.set_relative_location(newLoc)

        self.import_lights(MAPFile)

        self.refresh_geometry_flag_settings()
        ue.log("Created procedural mesh")

    def PositionListToFVector(self, position, performRotation=False):
        newVec = FVector(position[0], position[1], position[2])
        if performRotation:
            newVec = KismetMathLibrary.RotateAngleAxis(newVec, 90.0, FVector(1.0, 0.0, 0.0))
        return newVec

    def refresh_geometry_flag_settings(self):
        # Force the meshes to update their visibility based on their flags and materials
        for currentMesh in self.proceduralMeshComponents:
            #print(currentMesh.GetDisplayName())
            currentMesh.UpdateFlagSettings()
            pass

    def import_renderables_as_mesh_component(self, name: str, renderables: [RenderableArray], shift_origin, parent_component):
        """Will import a list of renderables into a single Mesh Component.
        shift_origin will determine whether or not to recenter the vertices around a local origin and shift the mesh component
        parent_component is the component that the new mesh component will attach to. Currently cannot be None.
        Returns a mesh component"""

        # Treat each geometryObject as a single component
        newPMC = self.uobject.add_actor_component(CustomProceduralMeshComponent, name, parent_component)
        self.uobject.add_instance_component(newPMC)
        self.uobject.modify()
        self.proceduralMeshComponents.append(newPMC)

        currentGeoObjAABB = AxisAlignedBoundingBox()

        # Calculate AABBs for each renderable
        for renderable in renderables:
            rAABB = renderable.calculate_AABB()
            currentGeoObjAABB = currentGeoObjAABB.merge(rAABB)

        # Calculate the offset for this GeometryObject
        currentAABBLoc = currentGeoObjAABB.get_center_position()
        offsetVec = FVector(currentAABBLoc[0], currentAABBLoc[1], currentAABBLoc[2])
        # Rotate offset to match unreals coordinate system
        offsetVec = KismetMathLibrary.RotateAngleAxis(offsetVec, 90.0, FVector(1.0, 0.0, 0.0))
        if shift_origin:
            newPMC.set_relative_location(offsetVec)

        # Adjust the world AABB
        # Only consider objects very far away for the world AABB, since dynamic objects like doors are very close to the origin, whereas static elements are over 50,000 units away
        # TODO: Use a similar check to set elements to static or moveable
        if offsetVec.length() > 1000.0:
            self.worldAABB = self.worldAABB.merge(currentGeoObjAABB)

        # Merge renderables with the same material index
        # Rogue spear maps in particular seem to have meshes broken up to each polygon. Collapsing these into a single mesh significantly reduces draw calls.
        mergedRenderables = {}
        for renderable in renderables:
            if renderable.materialIndex in mergedRenderables:
                # There is already a renderable using this material index
                masterRenderable = mergedRenderables[renderable.materialIndex]
                masterRenderable.merge(renderable)
            else:
                mergedRenderables[renderable.materialIndex] = renderable

        # Import each renderable as a mesh now
        for key, renderable in mergedRenderables.items():
            if shift_origin:
                # If shifting the origin, calculate the offset by the AABB and invert it
                inverseLocation = []
                for el in currentAABBLoc:
                    inverseLocation.append(el * -1)
                # Translate the vertices by the inverted offset so they are centred around the origin
                renderable.translate(inverseLocation)
            self.import_renderable(newPMC, renderable, self.generatedMaterials)

        return newPMC

    def import_renderable(self, mesh_component, renderable, materials):
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
        if renderable.UVs is not None:
            for UV in renderable.UVs:
                uvArray.append(FVector2D(UV[0], UV[1]))

        colorArray = []
        if renderable.vertexColors is not None:
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

        newMeshSectionIdx = mesh_component.AutoCreateMeshSection(vertexArray, indexArray, normalArray, UV0=uvArray, VertexColors=colorArray, bCreateCollision=True)
        newMeshSectionIdx = mesh_component.GetLastCreatedMeshIndex()

        if renderable.materialIndex != R6Constants.UINT_MAX:
            mesh_component.SetMaterial(newMeshSectionIdx, materials[renderable.materialIndex])

    # # properties can only be set starting from begin play
    # def ReceiveBeginPlay(self):
    #     """Called when the actor is beginning play, or the world is beginning play"""
    #     self.LoadMap()
