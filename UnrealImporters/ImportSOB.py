"""This moduled defines classes and functions related to importing RSE assets into Unreal"""
import os
import logging
from typing import List, Dict
from PIL import Image as PILImage # type: ignore

# pylint: disable=no-member, broad-except
# Disabled no-member for this module since a lot of functionality exposed by UnrealEnginePython doesn't exist outside of unreal and generates false positives
# Disabled unresolved-import since many imports are only available at runtime
# Disabled broad-except as UnrealEnginePython only raises the Exception class.

import unreal_engine as ue # type: ignore
from unreal_engine.classes import SceneComponent, RSEGeometryComponent, KismetMathLibrary, MaterialInterface, Texture2D, RSEPortalMeshComponent # type: ignore
from unreal_engine import FVector, FVector2D, FColor, FLinearColor # type: ignore
from unreal_engine.enums import EPixelFormat, TextureAddress # type: ignore

from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import RSBImageReader
from RainbowFileReaders import R6Constants
from RainbowFileReaders import R6Settings
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition
from RainbowFileReaders.R6Constants import RSEGameVersions
from RainbowFileReaders.RenderableArray import RenderableArray, merge_renderables_by_material, shift_origin_of_renderables
from RainbowFileReaders.MathHelpers import AxisAlignedBoundingBox
from RainbowFileReaders.MAPLevelReader import RSEMAPPortalList
from RainbowFileReaders.RSMAPStructures import RSMAPGeometryObject
from RainbowFileReaders.RSEGeometryDataStructures import R6GeometryObject

from UnrealImporters import ImporterSettings

log = logging.getLogger(__name__)

ue.log('Initializing SOB File importer')

bp_RoomComponent = None

def refresh_class_references():
    """Called to load blueprint class references. Can be run at anytime to ensure class references are valid."""
    # pylint: disable=global-statement
    # Global statement warning disabled in this function as this is a work around for delayed loading of blueprint classes
    try:
        global bp_RoomComponent
        bp_RoomComponent = ue.find_class('BP_RoomComponent_C')
    except Exception:
        ue.log_warning("Unable to load class BP_RoomComponent_C. This happens during cooking. If this is happening during gameplay something has gone wrong.")

refresh_class_references()

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
    else:
        if materialDefinition.opacity < 1.0:
            blendMode = "alpha"

    materialRequired = "MI_ShermanRommel_" + blendMode
    if bTwoSided:
        materialRequired += "_twosided"

    return materialRequired

def import_renderable(newRSEGeoComp, renderable: RenderableArray, materials: List[RSEMaterialDefinition]):
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

    newMeshSectionIdx = newRSEGeoComp.AutoCreateMeshSection(vertexArray, indexArray, normalArray, UV0=uvArray, VertexColors=colorArray, bCreateCollision=True)
    newMeshSectionIdx = newRSEGeoComp.GetLastCreatedMeshIndex()

    if renderable.materialIndex != R6Constants.UINT_MAX:
        newRSEGeoComp.SetMaterial(newMeshSectionIdx, materials[renderable.materialIndex])

def set_rse_geometry_flags_on_mesh_component(mesh_component, collision_only: bool, flags_dict: Dict[str, bool]):
    """Set flags from a dictionary that contains geometry flags for an object"""
    if mesh_component is None:
        return

    mesh_component.bCollisionOnly = collision_only

    if flags_dict is not None:
        mesh_component.SetRSEGeometryFlags(True,
                                           flags_dict["GF_CLIMBABLE"],
                                           flags_dict["GF_NOCOLLIDE2D"],
                                           flags_dict["GF_INVISIBLE"],
                                           flags_dict["GF_UNKNOWN2"],
                                           flags_dict["GF_FLOORPOLYGON"],
                                           flags_dict["GF_NOCOLLIDE3D"],
                                           flags_dict["GF_UNKNOWN4"],
                                           flags_dict["GF_NOTSHOWNINPLAN"])

def arrayvector_to_fvector(position: List[float], performRotation: bool=False):
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
            image = PILImage.open(PNGFilename)
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
        if image.mode == 'RGB':
            image.putalpha(255)
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

    def get_unreal_master_material(self, material_name: str) -> MaterialInterface:
        """Gets an unreal material for use. If it's not already loaded, it will load it automatically and cache it for next time"""
        if material_name in self.loadedParentMaterials:
            return self.loadedParentMaterials[material_name]

        materialFullPath = "/Game/Rainbow/MasterMaterials/{matname}.{matname}".format(matname=material_name)
        loadedMaterial = None
        try:
            loadedMaterial = ue.load_object(MaterialInterface, materialFullPath)
        except Exception:
            ue.log_warning(f"Failed to load material: {materialFullPath} for materialDefinition: {material_name}")
            raise
        self.loadedParentMaterials[material_name] = loadedMaterial
        return loadedMaterial

    def LoadMaterial(self, materialDefinition: RSEMaterialDefinition):
        """Creates a single material instance from a material definition"""
        verbose = False
        if materialDefinition.texture_name.string.startswith("cl02_spray1"):
            verbose = True
        parentMaterialName = determine_parent_material_required(materialDefinition)
        parentMaterial = self.get_unreal_master_material(parentMaterialName)
        if verbose:
            ue.log("=====================")
            ue.log(materialDefinition.texture_name.string)
            ue.log(parentMaterialName)
        if parentMaterial is None:
            ue.log("Error, could not load parent material: {}".format(parentMaterialName))
            self.generatedMaterials.append(None)
            return None
        mid = self.uobject.create_material_instance_dynamic(parentMaterial) # type: ignore

        mid.set_material_scalar_parameter("EmissiveStrength", materialDefinition.emissiveStrength)
        mid.set_material_scalar_parameter("SpecularLevel", materialDefinition.specularLevel)
        mid.set_material_scalar_parameter("Opacity", materialDefinition.opacity)

        colorKeyRGB = None

        if materialDefinition.CXPMaterialProperties is not None:
            if materialDefinition.CXPMaterialProperties.blendMode == "colorkey":
                cxpProps = materialDefinition.CXPMaterialProperties
                colorKeyRGB = cxpProps.colorkey

        if colorKeyRGB is None:
            # set this to out of range values, so no special case handling is needed elsewhere as the comparison will always fail, and work will be skipped
            colorKeyRGB = [300, 300, 300]

        # Determine, load and Set diffuse texture
        if materialDefinition.texture_name.string == "NULL":
            mid.set_material_scalar_parameter('UseVertexColor', 1.0)
        else:
            mid.set_material_scalar_parameter('UseVertexColor', 0.0)
            texturesToLoad = []
            # Add the first texture
            texturesToLoad.append(materialDefinition.texture_name.string)
            # Gather all other texture names
            if materialDefinition.CXPMaterialProperties is not None:
                for additionalTexture in materialDefinition.CXPMaterialProperties.animAdditionalTextures:
                    texturesToLoad.append(additionalTexture)
            # Load all textures
            LastTexture = None
            for i, currentTextureName in enumerate(texturesToLoad):
                foundTexture = None
                for path in self.texturePaths:
                    foundTexture = R6Settings.find_texture(currentTextureName, path)
                    if foundTexture is not None:
                        break
                if foundTexture is not None:
                    #This assumes all textures in a flipbook use the same colorkey
                    LastTexture = self.LoadTexture(foundTexture, colorKeyRGB[0], colorKeyRGB[1], colorKeyRGB[2], materialDefinition.textureAddressMode)
                    if LastTexture is not None:
                        currentTextureSlotName = "DiffuseTexture" + str(i)
                        #Add texture to appropriate slot
                        mid.set_material_texture_parameter(currentTextureSlotName,LastTexture)
                else:
                    ue.log("Failed to find texture: " + currentTextureName)

            #Setup animation properties
            if materialDefinition.CXPMaterialProperties is not None:
                if materialDefinition.CXPMaterialProperties.animated:
                    mid.set_material_scalar_parameter("AnimationInterval", materialDefinition.CXPMaterialProperties.animInterval)
                    numFrames = len(texturesToLoad)
                    ue.log("Number of animation frames: " + str(numFrames))
                    mid.set_material_scalar_parameter("NumberOfAnimationFrames", numFrames)
                else:
                    mid.set_material_scalar_parameter("AnimationInterval", 0.1)
                    mid.set_material_scalar_parameter("NumberOfAnimationFrames", 1)

                if materialDefinition.CXPMaterialProperties.scrolling:
                    mid.set_material_scalar_parameter("ScrollSpeedX", materialDefinition.CXPMaterialProperties.scrollParams[1])
                    mid.set_material_scalar_parameter("ScrollSpeedY", materialDefinition.CXPMaterialProperties.scrollParams[2])

        return mid

    def LoadMaterials(self):
        """Creates Unreal Material Instances for each material definition"""
        self.texturePaths = R6Settings.get_relevant_global_texture_paths(self.filepath)
        for path in self.texturePaths:
            ue.log("Using Texture Path: " + path)

        for matDef in self.materialDefinitions:
            mid = self.LoadMaterial(matDef)
            self.generatedMaterials.append(mid)

class SOBModel(RSEResourceLoader):
    """Loads an RSE SOB file into unreal assets"""
    # constructor adding a component
    def __init__(self):
        super().__init__()
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

            ue.log("Processing geoobj: " + name)
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
        self.defaultSceneComponent = self.uobject.get_actor_component_by_type(SceneComponent)
        #self.defaultSceneComponent.own()

        self.proceduralMeshComponents = []
        # All AABBs for each static geometry object should be added to this worldAABB
        # This will allow an offset to be calculated to shift the map closer to the world origin, buying back precision
        self.worldAABB = AxisAlignedBoundingBox()
        self.shift_origin = True
        refresh_class_references()

    def tick(self, delta_time: float):
        """Called every frame"""

    def import_level_heights(self, MAPFile: MAPLevelReader.MAPLevelFile):
        """Imports a level height definition from the map data structure"""
        for level in MAPFile.planningLevelList.planningLevels:
            adjustedHeight = level.floorHeight - self.worldOffsetVec[2]
            #self.worldOffsetVec[2]
            self.uobject.AddLevelHeight(adjustedHeight) # type: ignore

    def import_r6_lights(self, MAPFile: MAPLevelReader.MAPLevelFile):
        """Imports lights in the rainbow six format light list"""
        #Import lightlist
        for r6LightDef in MAPFile.lightList.lights:
            # Place lamp to a specified location
            position = arrayvector_to_fvector(r6LightDef.position, True)
            if self.shift_origin:
                position = position - self.worldOffsetVec

            color = []
            for color_el in r6LightDef.color:
                color.append(color_el / 255.0)
            linearColor = FLinearColor(color[0], color[1], color[2])

            constAtten = r6LightDef.constantAttenuation
            linAtten = r6LightDef.linearAttenuation
            quadAtten = r6LightDef.quadraticAttenuation
            energy = r6LightDef.energy
            falloff = r6LightDef.falloff
            lightType = r6LightDef.type
            lightName = r6LightDef.name_string.string
            roomNumber = str(int(lightName.split("_")[-1]))
            self.defaultSceneComponent = self.uobject.get_actor_component_by_type(SceneComponent) # type: ignore
            #roomAttachment = self.defaultSceneComponent
            roomAttachment = None
            if roomNumber in self.rooms:
                roomAttachment = self.rooms[roomNumber]
            else:
                ue.log("No room for light: " + lightName + " roomnumber: " + roomNumber)

            self.uobject.AddPointlight(position, linearColor, constAtten, linAtten, quadAtten, falloff, energy, lightType, lightName, roomAttachment) # type: ignore

    def import_rs_lights(self, MAPFile: MAPLevelReader.MAPLevelFile):
        """Imports lights imported via DMP files for Rogue Spear"""
        #Import DMP lights
        if MAPFile.dmpLights is not None:
            for rsLightDef in MAPFile.dmpLights.lights:
                # Place lamp to a specified location
                position = arrayvector_to_fvector(rsLightDef.position, True)
                if self.shift_origin:
                    position = position - self.worldOffsetVec

                color = []
                for color_el in rsLightDef.diffuseColor:
                    color.append(color_el)
                linearColor = FLinearColor(color[0], color[1], color[2])

                constAtten = rsLightDef.constantAttenuation
                linAtten = rsLightDef.linearAttenuation
                quadAtten = rsLightDef.quadraticAttenuation
                energy = rsLightDef.energy
                falloff = rsLightDef.falloff
                lightType = rsLightDef.lightType
                lightName = rsLightDef.name_string.string

                self.uobject.AddPointlight(position, linearColor, constAtten, linAtten, quadAtten, falloff, energy, lightType, lightName, None) # type: ignore


    def import_lights(self, MAPFile: MAPLevelReader.MAPLevelFile):
        """Import every light in the map file, both RS and R6 types"""
        self.import_r6_lights(MAPFile)
        self.import_rs_lights(MAPFile)

    def shift_origin_of_new_renderables(self, renderables: List[RenderableArray]):
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
                rsemeshcomponent.SetProjectilePassFlags(material.CXPMaterialProperties.gunpass,
                                                        material.CXPMaterialProperties.grenadepass)

    def import_rogue_spear_geometry_object(self, geoObjectDefinition: RSMAPGeometryObject, geoObjComponent):
        """Imports geometry from a rogue spear map geometryObject definition"""
        name = geoObjectDefinition.name_string.string

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
        collisionComponent = self.uobject.add_actor_component(SceneComponent, collisionName, self.defaultSceneComponent) # type: ignore
        collisionData = geoObjectDefinition.geometryData.collisionInformation
        for i, collMesh in enumerate(collisionData.collisionMeshDefinitions):
            if collMesh.geometryFlagsEvaluated["GF_INVISIBLE"] is True:
                #Do not process invalid and unused meshes
                continue
            subCollisionName = collisionName + "_idx" + str(i)
            renderable = collisionData.generate_renderable_array_for_collisionmesh(collMesh, geoObjectDefinition.geometryData)
            newMeshComponent = self.import_renderables_as_mesh_component(subCollisionName, [renderable], collisionComponent)

            set_rse_geometry_flags_on_mesh_component(newMeshComponent, True, collMesh.geometryFlagsEvaluated)

    def import_rainbow_six_geometry_object(self, geoObjectDefinition: R6GeometryObject, geoObjComponent):
        """Imports geometry from a rainbow six map geometryObject definition"""
        name = geoObjectDefinition.name_string.string

        for srcMeshIdx, sourceMesh in enumerate(geoObjectDefinition.meshes):
            renderableName = name + "_" + sourceMesh.name_string.string + "_" + str(srcMeshIdx)
            currRenderables = geoObjectDefinition.generate_renderable_arrays_for_mesh(sourceMesh)

            mergedRenderables = merge_renderables_by_material(currRenderables)
            offsetVec = self.shift_origin_of_new_renderables(mergedRenderables)

            newMeshComponent = self.import_renderables_as_mesh_component(renderableName, mergedRenderables, geoObjComponent)
            newMeshComponent.set_relative_location(offsetVec)
            self.objectsToShift.append(newMeshComponent)

            set_rse_geometry_flags_on_mesh_component(newMeshComponent, False, sourceMesh.geometryFlagsEvaluated)
            geoObjComponent.AddMesh(newMeshComponent)

    def import_portals(self, portallist: RSEMAPPortalList):
        """Imports portals and creates appropriate static meshes for them."""
        self.defaultSceneComponent = self.uobject.get_actor_component_by_type(SceneComponent) # type: ignore
        portalParentComponent = self.uobject.add_actor_component(SceneComponent, "portals", self.defaultSceneComponent) # type: ignore
        portalComponents = []
        for portal in portallist.portals:
            portalRA = portal.generate_renderable_array_object()
            offsetVec = self.shift_origin_of_new_renderables([portalRA])
            newMeshComponent = self.import_renderables_as_mesh_component(portal.name_string.string, [portalRA], portalParentComponent, RSEPortalMeshComponent)
            newMeshComponent.set_relative_location(offsetVec)
            newMeshComponent.roomA = portal.roomA
            newMeshComponent.roomB = portal.roomB
            portalComponents.append(newMeshComponent)

        self.uobject.RefreshPortals(portalComponents) # type: ignore

        return portalComponents

    def import_rooms(self, MAPFile: MAPLevelReader.MAPLevelFile):
        """Imports room volumes to for portals and occlusion checking"""
        for room in MAPFile.roomList.rooms:
            for levelDef in room.shermanLevels:
                aabb = levelDef.get_aabb()
                vertex = aabb.get_center_position()
                center = FVector(vertex[0], vertex[1], vertex[2])
                center = KismetMathLibrary.RotateAngleAxis(center, 90.0, FVector(1.0, 0.0, 0.0))
                center = center - self.worldOffsetVec
                vertex = aabb.get_size()
                scale = FVector(vertex[0], vertex[1], vertex[2])
                scale = KismetMathLibrary.RotateAngleAxis(scale, 90.0, FVector(1.0, 0.0, 0.0))
                self.uobject.AddRoomTrigger(levelDef.nameString, center, scale) # type: ignore
        self.uobject.RefreshRoomTriggersDebug() # type: ignore

    def load_map(self):
        """Wrapper function for load_map_actual, with some optional profiling code"""
        #import cProfile
        #cProfile.runctx('self.load_map_actual()', globals(), locals())
        self.load_map_actual()

    def load_map_actual(self) -> None:
        """Loads the file and creates appropriate assets in unreal"""
        #self.filepath = ImporterSettings.map_file_path
        self.filepath = self.uobject.mappath # type: ignore
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
        self.rooms = {}

        for _, geoObjectDefinition in enumerate(MAPFile.geometryObjects):
            name = geoObjectDefinition.name_string.string
            if name in usedNames:
                ue.log("Duplicate name! " + name)
            else:
                usedNames.append(name)

            #ue.log("Processing geoobj: " + name)
            self.defaultSceneComponent = self.uobject.get_actor_component_by_type(SceneComponent) # type: ignore
            geoObjComponent = self.uobject.add_actor_component(bp_RoomComponent, name, self.defaultSceneComponent) # type: ignore
            self.rooms[name] = geoObjComponent
            self.uobject.add_instance_component(geoObjComponent) # type: ignore
            self.uobject.modify() # type: ignore
            self.objectComponents.append(geoObjComponent)

            if MAPFile.gameVersion == RSEGameVersions.RAINBOW_SIX:
                if isinstance(geoObjectDefinition, R6GeometryObject):
                    self.import_rainbow_six_geometry_object(geoObjectDefinition, geoObjComponent)
            else: # Rogue spear
                if isinstance(geoObjectDefinition, RSMAPGeometryObject):
                    self.import_rogue_spear_geometry_object(geoObjectDefinition, geoObjComponent)

        self.objectsToShift.extend(self.import_portals(MAPFile.portalList))

        if self.shift_origin:
            ue.log("Recentering objects")
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
            currentMesh.UpdateRSEFlagSettings()

    def import_renderables_as_mesh_component(self, name: str, renderables: List[RenderableArray], parent_component, mesh_component_type=RSEGeometryComponent):
        """Will import a list of renderables into a single Mesh Component.
        parent_component is the component that the new mesh component will attach to. Currently cannot be None.
        Returns a mesh component"""

        # Treat each geometryObject as a single component
        newRSEGeoComp = self.uobject.add_actor_component(mesh_component_type, name, parent_component) # type: ignore
        self.uobject.add_instance_component(newRSEGeoComp)  # type: ignore
        self.uobject.modify() # type: ignore
        if mesh_component_type is RSEGeometryComponent:
            self.proceduralMeshComponents.append(newRSEGeoComp)

        # Import each renderable as a mesh now
        for renderable in renderables:
            import_renderable(newRSEGeoComp, renderable, self.generatedMaterials)

        return newRSEGeoComp
