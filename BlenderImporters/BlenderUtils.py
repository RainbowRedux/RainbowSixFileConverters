import bpy
import bmesh

import os

from RainbowFileReaders import R6Settings
from RainbowFileReaders import R6Constants
from RainbowFileReaders.R6Constants import UINT_MAX
from RainbowFileReaders.MathHelpers import normalize_color, sanitize_float
from RainbowFileReaders.SOBModelReader import SOBAlphaMethod

def flip_normals_on_object(blendObject):
    #https://blenderartists.org/t/script-to-flip-normals-for-multiple-objects/533443/2
    bpy.context.scene.objects.active = blendObject
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals() # just flip normals
    bpy.ops.object.mode_set()

def set_blender_render_unit_scale_options():
    ONE_KILOMETER = 100 * 1000 #100cm in a meter, 1000m in a km
    TEN_CENTIMETERS = 10

    # https://blender.stackexchange.com/a/38613
    if bpy.context.scene.camera is not None:
        bpy.data.cameras[bpy.context.scene.camera.name].clip_end = ONE_KILOMETER
        bpy.data.cameras[bpy.context.scene.camera.name].clip_start = TEN_CENTIMETERS

    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_end = ONE_KILOMETER
                    s.clip_start = TEN_CENTIMETERS

    #set scene scale
    # https://blenderartists.org/t/how-to-set-units-and-render-engine-via-script/537823/2
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.system_rotation = 'DEGREES'
    bpy.context.scene.unit_settings.scale_length = 0.01

def set_environment_lighting_enabled(bEnabled):
    for world in bpy.data.worlds:
        world.light_settings.use_environment_light = bEnabled

def setup_blank_scene():
    #bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.read_factory_settings()
    set_blender_render_unit_scale_options()
    set_environment_lighting_enabled(True)
    pass

def create_blender_mesh_object(name, existingMesh=None):
    newMesh = existingMesh
    if newMesh is None:
        newMesh = bpy.data.meshes.new(name + 'Mesh')
    newObject = bpy.data.objects.new(name, newMesh)
    newObject.location = (0,0,0)
    newObject.show_name = True
    # Link object to scene
    bpy.context.scene.objects.link(newObject)
    return (newMesh, newObject)

def clone_mesh_object_with_specified_faces(newObjectName, faceIndices, originalObject ):
    #Copy master mesh into new object
    newObjMeshCopy = originalObject.data.copy()
    newObjMeshCopy, newSubBlendObject = create_blender_mesh_object(newObjectName, newObjMeshCopy)
    
    #select the object
    bpy.context.scene.objects.active = newSubBlendObject

    bpy.ops.object.mode_set(mode='EDIT')

    bmDelFaces = bmesh.from_edit_mesh(newObjMeshCopy)

    #https://blender.stackexchange.com/a/31750
    bmDelFaces.faces.ensure_lookup_table()
    
    selectedFaces = []
    for i in range(len(bmDelFaces.faces)):
        if i in faceIndices:
            pass
        else:
            selectedFaces.append(bmDelFaces.faces[i])

    # https://blender.stackexchange.com/a/1542
    DEL_FACES = 5
    DEL_ALL = 6
    bmesh.ops.delete(bmDelFaces, geom=selectedFaces, context=DEL_FACES)  

    # Push the changes back to edit mode and change to object mode
    bmesh.update_edit_mesh(newObjMeshCopy, True)
    bpy.ops.object.mode_set(mode='OBJECT')

    numFacesToKeep = len(faceIndices)
    numFacesRemaining = len(newSubBlendObject.data.polygons)
    print("Number of faces to select: " + str(numFacesToKeep))
    print("Number of faces left: " + str(numFacesRemaining))

    if numFacesRemaining != numFacesToKeep:
        print("Face count mismatch!")
        #errorCount += 1
        #errorList.append(newObjectName + " missing " + str(numFacesToKeep - numFacesRemaining))
        #TODO: Add a way to log errors that can be summarised at the end of a set of operations
        #raise Exception('Unable to create correct object')

    return newSubBlendObject

def attach_materials_to_blender_object(blenderObject, materials):
    #This attaches all materials to the mesh, which is excessive in some circumstances
    for material in materials:
        blenderObject.data.materials.append(material)

def add_mesh_geometry(mesh, vertices, faces):
    #use this over bmesh, as it will allow faces that share vertices with different windings
    mesh.from_pydata(vertices, [], faces)

    # Update mesh with new data
    mesh.update(calc_edges=True)

def remove_unused_materials_from_mesh_object(objectToClean):
    objectToClean.data.materials

    materialIndicesInUse = []

    for i in range(len(objectToClean.data.polygons)):
        poly = objectToClean.data.polygons[i]
        materialIndicesInUse.append(poly.material_index)

    materialIndicesInUse.sort()

    numMaterials = len(objectToClean.data.materials)
    j = 0
    for i in range(numMaterials):
        if i not in materialIndicesInUse:
            objectToClean.data.materials.pop(j, True)
            j -= 1
        j += 1

def create_blender_materials_from_list(materialList, filepath, gameDataPath):
    blenderMaterials = []

    for materialSpec in materialList:
        newMaterial = create_material_from_RSE_specification(materialSpec, filepath, gameDataPath)
        blenderMaterials.append(newMaterial)
    
    return blenderMaterials

def fixup_texture_name(filename):
    ext = filename.lower()[-4:]
    newfilename = filename
    if ext == ".bmp" or ext == ".rsb" or ext == ".tga":
        newfilename = newfilename[:-4]
        newfilename += ".PNG"
    return newfilename


def find_texture(filename, dataPath):
    if filename.lower() == "null":
        return None
    newfilename = fixup_texture_name(filename)
    result = None
    for root, dirs, files in os.walk(dataPath):
        for name in files:
            # Compare lowercase versions since windows is case-insensitive
            if name.lower() == newfilename.lower():
                result = os.path.join(root, name)
            if result is None and name.startswith("TGA"):
                if name.lower()[3:] == newfilename.lower():
                    result = os.path.join(root, name)

        for name in dirs:
            pass
    return result


def create_material_from_RSE_specification(materialSpecification, filepath, gameDataPath):
    """Creates a material from an RSE specification.
    This does ignore some values that don't map well to PBR and don't influence model behaviour much.
    Materials will be more finely tuned in the game engine.
    
    materialSpecification is an RSEMaterialDefinition as read by RSEModelReader

    gameDataPath is meant to be the Data folder within the games installation
        directory, as that directory structure is used when loading textures"""

    # set new material to variable
    newMaterial = bpy.data.materials.new(name=materialSpecification.materialName)
    
    globalTexturePath = os.path.join(gameDataPath, R6Settings.paths["TexturePath"])
    globalTexturePath = os.path.normpath(globalTexturePath)

    textureName = materialSpecification.textureName
    #load from model/map local directory first
    texToLoad = find_texture(textureName, filepath)
    # if unable to find the texture, find in the global texture path
    if texToLoad is None:
        texToLoad = find_texture(textureName, globalTexturePath)
    if texToLoad is None:
        print("Failed to find texture: " + str(textureName))
    else:
        print("Final texture to load: " + str(texToLoad))

    if texToLoad is not None:
        # Texture loading code adapted from https://stackoverflow.com/q/19076062
        # Load the image
        texImage = bpy.data.images.load(texToLoad)
        # Create texture from image
        newTexture = bpy.data.textures.new('ColorTex', type = 'IMAGE')
        newTexture.image = texImage

        # Add texture slot for color texture
        textureSlot = newMaterial.texture_slots.add()
        textureSlot.texture = newTexture

        textureSlot.use_map_color_diffuse = True
        textureSlot.texture_coords = 'UV'

        if materialSpecification.alphaMethod != SOBAlphaMethod.SAM_Opaque:
            newTexture.use_alpha = True
            textureSlot.use_map_alpha = True
            textureSlot.alpha_factor = materialSpecification.opacity

    if materialSpecification.alphaMethod != SOBAlphaMethod.SAM_Opaque:
        print(materialSpecification.materialName)
        print(str(materialSpecification.alphaMethod))
        print(str(SOBAlphaMethod.SAM_Opaque))
        newMaterial.use_transparency = True
        #Blenders material transparency method is different to how masked alpha would work in a game engine,
        # this still provides alpha blending, but if you use Z method the transparent part of the surface
        # still has specular properties. In this instance, MASK provides expected results
        newMaterial.transparency_method = 'MASK'

        if texToLoad is not None:
            newMaterial.alpha = 0.0
        else:
            #TODO: Check that opacity is not used when alphaMethod == 1 or SAM_Opaque
            newMaterial.alpha = materialSpecification.opacity

    # TODO: work out if materialSpecification.ambient should be averaged and applied
    # to newMaterial.ambient, or if it's for the lighting model that might be
    # specified in materialSpecification.unknown2
    if materialSpecification.normalizedColors:
        newMaterial.diffuse_color = materialSpecification.diffuse[0:3]  # change color
        newMaterial.specular_color = materialSpecification.specular[0:3]
    else:
        newMaterial.diffuse_color = normalize_color(materialSpecification.diffuse)[0:3]  # change color
        newMaterial.specular_color = normalize_color(materialSpecification.specular)[0:3]
    newMaterial.specular_intensity = materialSpecification.specularLevel
    newMaterial.use_vertex_color_light = True


    return newMaterial
