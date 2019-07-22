"""This moduled defines classes and functions related to importing RSE assets into Unreal"""
import os
import PIL
# Pylint disabled error W0611 as this is actually due to python not loading submodules by default
from PIL import Image # pylint: disable=W0611

import unreal_engine as ue
from unreal_engine.classes import SceneComponent, CustomProceduralMeshComponent, KismetMathLibrary, MaterialInterface, Texture2D
from unreal_engine import FVector, FVector2D, FColor, FLinearColor
from unreal_engine.enums import EPixelFormat, TextureAddress

from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import RSBImageReader
from RainbowFileReaders import R6Constants
from RainbowFileReaders import R6Settings
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition
from RainbowFileReaders.R6Constants import RSEGameVersions
from RainbowFileReaders.RenderableArray import RenderableArray, merge_renderables_by_material, shift_origin_of_renderables
from RainbowFileReaders.MathHelpers import AxisAlignedBoundingBox

from UnrealImporters import ImporterSettings

ue.log('Initializing SOB File importer')

def determine_parent_material_required(materialDefinition: RSEMaterialDefinition) -> (str):
    """Assesses the material definition and determines the correct parent material to use"""
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

def import_renderable(mesh_component, renderable, materials):
    """Adds the specified renderable as a mesh section to the supplied procedural mesh component"""
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
            uvArray.append(FVector2D(UV[0], UV[1] + 1.0))

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

def set_rse_geometry_flags_on_mesh_component(mesh_component, collision_only, flags_dict):
    """Set flags from a dictionary that contains geometry flags for an object"""
    if mesh_component is None:
        return

    mesh_component.bCollisionOnly = collision_only
    mesh_component.bHasRSEGeometryFlags = True

    if flags_dict is not None:
        mesh_component.bGF_Climbable = flags_dict["GF_CLIMBABLE"]
        mesh_component.bGF_NoCollide2D = flags_dict["GF_NOCOLLIDE2D"]
        mesh_component.bGF_Invisible = flags_dict["GF_INVISIBLE"]
        mesh_component.bGF_Unknown2 = flags_dict["GF_UNKNOWN2"]
        mesh_component.bGF_FloorPolygon = flags_dict["GF_FLOORPOLYGON"]
        mesh_component.bGF_NoCollide3D = flags_dict["GF_NOCOLLIDE3D"]
        mesh_component.bGF_Unknown4 = flags_dict["GF_UNKNOWN4"]
        mesh_component.bGF_NotShownInPlan = flags_dict["GF_NOTSHOWNINPLAN"]

def arrayvector_to_fvector(position, performRotation=False):
    """Converts a list of 3 floats into an unreal FVector class"""
    newVec = FVector(position[0], position[1], position[2])
    if performRotation:
        newVec = KismetMathLibrary.RotateAngleAxis(newVec, 90.0, FVector(1.0, 0.0, 0.0))
    return newVec

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

        textureAddressModeConstant = TextureAddress.TA_Wrap
        if textureAddressMode == 1: #WRAP
            textureAddressModeConstant = TextureAddress.TA_Wrap
        elif textureAddressMode == 2: #MIRROR
            textureAddressModeConstant = TextureAddress.TA_Mirror
        elif textureAddressMode == 3: #CLAMP
            #this should be CLAMP but many textures break when this is enabled.
            textureAddressModeConstant = TextureAddress.TA_Wrap
        else:
            ue.warn("WARNING: Unknown texture tiling method")

        newTexture.AddressX = textureAddressModeConstant
        newTexture.AddressY = textureAddressModeConstant

        self.loadedTextures[texturePath] = newTexture
        return newTexture

    def get_unreal_master_material(self, material_name: str) -> (MaterialInterface):
        """Gets an unreal material for use. If it's not already loaded, it will load it automatically and cache it for next time"""
        if material_name in self.loadedParentMaterials:
            return self.loadedParentMaterials[material_name]

        materialFullPath = "/Game/Rainbow/MasterMaterials/{matname}.{matname}".format(matname=material_name)
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
            parentMaterialName = determine_parent_material_required(matDef)
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
        self.shift_origin = False
        self.load_model()
        #self.proceduralMeshComponent = self.add_actor_component(CustomProceduralMeshComponent, 'ProceduralMesh')

    def load_model(self):
        """Loads the file and creates appropriate assets in unreal"""
        self.filepath = "D:/R6Data/TestData/ReducedGames/R6GOG/data/model/cessna.sob"
        SOBFile = SOBModelReader.SOBModelFile()
        SOBFile.read_file(self.filepath)
        numGeoObjects = len(SOBFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        ue.log("material definitions: " + str(len(SOBFile.materials)))
        self.materialDefinitions = SOBFile.materials
        self.LoadMaterials()

        for _, geoObj in enumerate(SOBFile.geometryObjects):
            name = geoObj.nameString

            print("Processing geoobj: " + name)
            geoObjComponent = self.uobject.add_actor_component(SceneComponent, name, self.defaultSceneComponent)
            self.uobject.add_instance_component(geoObjComponent)
            self.uobject.modify()
            self.objectComponents.append(geoObjComponent)

            for srcMeshIdx, sourceMesh in enumerate(geoObj.meshes):
                renderableName = name + "_" + sourceMesh.nameString + "_" + str(srcMeshIdx)
                currRenderables = geoObj.generate_renderable_arrays_for_mesh(sourceMesh)

                mergedRenderables = merge_renderables_by_material(currRenderables)

                newMeshComponent = self.import_renderables_as_mesh_component(renderableName, mergedRenderables, self.shift_origin, geoObjComponent)

                set_rse_geometry_flags_on_mesh_component(newMeshComponent, False, sourceMesh.geometryFlagsEvaluated)

    # properties can only be set starting from begin play
    def ReceiveBeginPlay(self):
        """Called when the actor is beginning play, or the world is beginning play"""
        #self.load_model()

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

    def tick(self, delta_time):
        """Called every frame"""
        pass

    def import_level_heights(self, MAPFile):
        for level in MAPFile.planningLevelList.planningLevels:
            adjustedHeight = level.floorHeight - self.worldOffsetVec[2]
            #self.worldOffsetVec[2]
            self.uobject.AddLevelHeight(adjustedHeight)

    def import_lights(self, MAPFile):
        """Import every light in the map file, both RS and R6 types"""
        self.uobject.SpawnLightActor()
        light_actor = self.uobject.LightActor

        #Import lightlist
        for lightDef in MAPFile.lightList.lights:
            # Place lamp to a specified location
            position = arrayvector_to_fvector(lightDef.position, True)
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

        #Import DMP lights
        if MAPFile.dmpLights is not None:
            for lightDef in MAPFile.dmpLights.lights:
                # Place lamp to a specified location
                position = arrayvector_to_fvector(lightDef.position, True)
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
                lightType = lightDef.lightType
                lightName = lightDef.nameString

                light_actor.AddPointlight(position, linearColor, constAtten, linAtten, quadAtten, falloff, energy, lightType, lightName)

    def shift_origin_of_new_renderables(self, renderables):
        """Calculates the combined bounds of the new renderables and shifts the origin
        Returns an offset vector in Unreal correct space"""
        if self.shift_origin:
            geometryBounds = shift_origin_of_renderables(renderables, 1000.0)
            offsetAmount = geometryBounds.get_center_position()
            offsetVec = FVector(offsetAmount[0], offsetAmount[1], offsetAmount[2])
            # Rotate offset to match unreals coordinate system
            offsetVec = KismetMathLibrary.RotateAngleAxis(offsetVec, 90.0, FVector(1.0, 0.0, 0.0))

            # Adjust the world AABB
            # Only consider objects very far away for the world AABB, since dynamic objects like doors are very close to the origin, whereas static elements are over 50,000 units away
            # TODO: Use a similar check to set elements to static or moveable
            if offsetVec.length() > 1000.0:
                self.worldAABB = self.worldAABB.merge(geometryBounds)

            return offsetVec
        return FVector(0.0, 0.0, 0.0)

    def apply_cxp_flags(self, rsemeshcomponent, materialIndex):
        """Add gunpass and grenadepass flags from CXP material info"""
        material = self.materialDefinitions[materialIndex]
        if material is not None:
            if material.CXPMaterialProperties is not None:
                if material.CXPMaterialProperties.gunpass:
                    rsemeshcomponent.bGunPass = True
                if material.CXPMaterialProperties.grenadepass:
                    rsemeshcomponent.bGrenadePass = True

    def import_rogue_spear_geometry_object(self, geoObjectDefinition, geoObjComponent):
        """Imports geometry from a rogue spear map geometryObject definition"""
        name = geoObjectDefinition.nameString

        #Setup all visual geometry
        geoObjRenderables = []
        for _, facegroup in enumerate(geoObjectDefinition.geometryData.faceGroups):
            renderable = geoObjectDefinition.geometryData.generate_renderable_array_for_facegroup(facegroup)
            geoObjRenderables.append(renderable)

        mergedRenderables = merge_renderables_by_material(geoObjRenderables)

        offsetVec = self.shift_origin_of_new_renderables(mergedRenderables)
        geoObjComponent.set_relative_location(offsetVec)
        self.objectsToShift.append(geoObjComponent)

        for renderable in mergedRenderables:
            renderableName = name + "_" + str(renderable.materialIndex)
            newMeshComponent = self.import_renderables_as_mesh_component(renderableName, [renderable], geoObjComponent)
            #adds flags like gunpass and grenadepass
            self.apply_cxp_flags(newMeshComponent, renderable.materialIndex)

        #setup collision geometry
        collisionName = name + "_collision"
        collisionComponent = self.uobject.add_actor_component(SceneComponent, collisionName, self.defaultSceneComponent)
        collisionData = geoObjectDefinition.geometryData.collisionInformation
        for i, collMesh in enumerate(collisionData.collisionMeshDefinitions):
            if collMesh.geometryFlagsEvaluated["GF_INVISIBLE"] is True:
                #Do not process invalid and unused meshes
                continue
            subCollisionName = collisionName + "_idx" + str(i)
            renderable = collisionData.generate_renderable_array_for_collisionmesh(collMesh, geoObjectDefinition.geometryData)
            newMeshComponent = self.import_renderables_as_mesh_component(subCollisionName, [renderable], collisionComponent)

            set_rse_geometry_flags_on_mesh_component(newMeshComponent, True, collMesh.geometryFlagsEvaluated)

    def import_rainbow_six_geometry_object(self, geoObjectDefinition, geoObjComponent):
        """Imports geometry from a rainbow six map geometryObject definition"""
        name = geoObjectDefinition.nameString

        for srcMeshIdx, sourceMesh in enumerate(geoObjectDefinition.meshes):
            renderableName = name + "_" + sourceMesh.nameString + "_" + str(srcMeshIdx)
            currRenderables = geoObjectDefinition.generate_renderable_arrays_for_mesh(sourceMesh)

            mergedRenderables = merge_renderables_by_material(currRenderables)
            offsetVec = self.shift_origin_of_new_renderables(mergedRenderables)

            newMeshComponent = self.import_renderables_as_mesh_component(renderableName, mergedRenderables, geoObjComponent)
            newMeshComponent.set_relative_location(offsetVec)
            self.objectsToShift.append(newMeshComponent)

            set_rse_geometry_flags_on_mesh_component(newMeshComponent, False, sourceMesh.geometryFlagsEvaluated)

    def import_portals(self, portallist):
        portalParentComponent = self.uobject.add_actor_component(SceneComponent, "portals", self.defaultSceneComponent)
        portalComponents = []
        for portal in portallist.portals:
            portalRA = portal.generate_renderable_array_object()
            offsetVec = self.shift_origin_of_new_renderables([portalRA])
            newMeshComponent = self.import_renderables_as_mesh_component(portal.nameString, [portalRA], portalParentComponent)
            newMeshComponent.set_relative_location(offsetVec)
            portalComponents.append(newMeshComponent)

        self.uobject.RefreshPortals(portalComponents)

        return portalComponents

    def import_rooms(self, MAPFile):
        print("Importing rooms")
        for room in MAPFile.roomList.rooms:
            print("Iterating room: " + room.nameString)
            for levelDef in room.shermanLevels:
                print("Iterating room level: " + levelDef.nameString)
                aabb = levelDef.get_aabb()
                vertex = aabb.get_center_position()
                center = FVector(vertex[0], vertex[1], vertex[2])
                center = KismetMathLibrary.RotateAngleAxis(center, 90.0, FVector(1.0, 0.0, 0.0))
                center = center - self.worldOffsetVec
                vertex = aabb.get_size()
                scale = FVector(vertex[0], vertex[1], vertex[2])
                scale = KismetMathLibrary.RotateAngleAxis(scale, 90.0, FVector(1.0, 0.0, 0.0))
                self.uobject.AddRoom(levelDef.nameString, center, scale)

    def load_map(self):
        #import cProfile
        #cProfile.runctx('self.load_map_actual()', globals(), locals())
        self.load_map_actual()

    def load_map_actual(self):
        """Loads the file and creates appropriate assets in unreal"""
        #self.filepath = ImporterSettings.map_file_path
        self.filepath = self.uobject.mappath
        #self.filepath = "D:/R6Data/TestData/ReducedGames/RSDemo/data/map/rm01/rm01.map"
        MAPFile = MAPLevelReader.MAPLevelFile()
        MAPFile.read_file(self.filepath)
        numGeoObjects = len(MAPFile.geometryObjects)
        ue.log("Num geoObjects: {}".format(numGeoObjects))

        ue.log("material definitions: " + str(len(MAPFile.materials)))
        self.materialDefinitions = MAPFile.materials
        self.LoadMaterials()

        usedNames = []
        self.objectComponents = []
        self.objectsToShift = []

        self.worldOffsetVec = FVector(0, 0, 0)

        for _, geoObjectDefinition in enumerate(MAPFile.geometryObjects):
            name = geoObjectDefinition.nameString
            if name in usedNames:
                ue.log("Duplicate name! " + name)
            else:
                usedNames.append(name)

            #print("Processing geoobj: " + name)
            geoObjComponent = self.uobject.add_actor_component(SceneComponent, name, self.defaultSceneComponent)
            self.uobject.add_instance_component(geoObjComponent)
            self.uobject.modify()
            self.objectComponents.append(geoObjComponent)

            if MAPFile.gameVersion == RSEGameVersions.RAINBOW_SIX:
                self.import_rainbow_six_geometry_object(geoObjectDefinition, geoObjComponent)
            else: # Rogue spear
                self.import_rogue_spear_geometry_object(geoObjectDefinition, geoObjComponent)

        self.objectsToShift.extend(self.import_portals(MAPFile.portalList))

        if self.shift_origin:
            print("Recentering objects")
            # Once all meshes have been imported, the WorldAABB will properly encapsulate the entire level,
            # and an appropriate offset can be calculated to bring each object back closer to the origin
            worldOffset = self.worldAABB.get_center_position()
            self.worldOffsetVec = FVector(worldOffset[0], worldOffset[1], worldOffset[2])
            self.worldOffsetVec = KismetMathLibrary.RotateAngleAxis(self.worldOffsetVec, 90.0, FVector(1.0, 0.0, 0.0))
            for geoObjComponent in self.objectsToShift:
                # Only shift static elements
                if geoObjComponent.get_relative_location().length() > 1000.0:
                    newLoc = geoObjComponent.get_relative_location() - self.worldOffsetVec
                    geoObjComponent.set_relative_location(newLoc)

        self.import_lights(MAPFile)

        self.refresh_geometry_flag_settings()

        self.import_level_heights(MAPFile)

        self.import_rooms(MAPFile)

        ue.log("Finished loading map")

    def refresh_geometry_flag_settings(self):
        """Force the meshes to update their visibility based on their flags and materials"""
        for currentMesh in self.proceduralMeshComponents:
            currentMesh.UpdateFlagSettings()

    def import_renderables_as_mesh_component(self, name: str, renderables: [RenderableArray], parent_component):
        """Will import a list of renderables into a single Mesh Component.
        parent_component is the component that the new mesh component will attach to. Currently cannot be None.
        Returns a mesh component"""

        # Treat each geometryObject as a single component
        newPMC = self.uobject.add_actor_component(CustomProceduralMeshComponent, name, parent_component)
        self.uobject.add_instance_component(newPMC)
        self.uobject.modify()
        self.proceduralMeshComponents.append(newPMC)

        # Import each renderable as a mesh now
        for renderable in renderables:
            import_renderable(newPMC, renderable, self.generatedMaterials)

        return newPMC
