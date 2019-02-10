"""
Defines generic and often used functions to perform operations in Blender
"""
import os
import math

import bpy
import bmesh
from bpy_extras import node_shader_utils

from RainbowFileReaders.R6Constants import RSEAlphaMethod
from RainbowFileReaders import R6Constants
from RainbowFileReaders.R6Settings import find_texture

def flip_normals_on_object(blendObject):
    """Flips the normals on specified object"""
    #https://blenderartists.org/t/script-to-flip-normals-for-multiple-objects/533443/2
    bpy.context.scene.objects.active = blendObject
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals() # just flip normals
    bpy.ops.object.mode_set()

def set_blender_render_unit_scale_options():
    """Sets the current blender scene to use 1cm units, and set appropriate clip planes"""
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

def setup_blank_scene():
    """Load a blank scene, unloading any existing imported models/materials etc"""
    #bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.read_factory_settings()
    set_blender_render_unit_scale_options()

def create_blender_blank_object(name):
    """Create a blank object in blender and link to the current scene"""
    newBlankObject = bpy.data.objects.new(name, None)
    newBlankObject.location = (0,0,0)
    newBlankObject.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(newBlankObject)

    return newBlankObject

def create_blender_mesh_object(name, existingMesh=None):
    """Create a blender object and associated mesh.
    If existingMesh is given a valid mesh, that will be used instead of creating a new one"""
    newMesh = existingMesh
    if newMesh is None:
        newMesh = bpy.data.meshes.new(name + 'Mesh')
    newObject = bpy.data.objects.new(name, newMesh)
    newObject.location = (0,0,0)
    newObject.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(newObject)
    return (newMesh, newObject)

def clone_mesh_object_with_specified_faces(newObjectName, faceIndices, originalObject ):
    """Clones a mesh, and then will delete all but the faces with the specified indices"""
    #Copy master mesh into new object
    newObjMeshCopy = originalObject.data.copy()
    newObjMeshCopy, newSubBlendObject = create_blender_mesh_object(newObjectName, newObjMeshCopy)
    newObjMeshCopy.name = newObjectName + "Mesh"

    #select the object
    newSubBlendObject.select_set(True)
    bpy.context.view_layer.objects.active = newSubBlendObject

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

    bmesh.ops.delete(bmDelFaces, geom=selectedFaces, context="FACES")

    # Push the changes back to edit mode and change to object mode
    bmesh.update_edit_mesh(newObjMeshCopy, True)
    bpy.ops.object.mode_set(mode='OBJECT')

    numFacesToKeep = len(faceIndices)
    numFacesRemaining = len(newSubBlendObject.data.polygons)

    if numFacesRemaining != numFacesToKeep:
        print("Face count mismatch!")
        #errorCount += 1
        #errorList.append(newObjectName + " missing " + str(numFacesToKeep - numFacesRemaining))
        #TODO: Add a way to log errors that can be summarised at the end of a set of operations
        #raise Exception('Unable to create correct object')

    return newSubBlendObject

def attach_materials_to_blender_object(blenderObject, materials):
    """Adds all materials in list to the specified blender object"""
    for material in materials:
        blenderObject.data.materials.append(material)

def add_mesh_geometry(mesh, vertices, faces):
    """Adds specified faces and vertices to the specified mesh"""
    #use this over bmesh, as it will allow faces that share vertices with different windings
    mesh.from_pydata(vertices, [], faces)

    # Update mesh with new data
    mesh.update(calc_edges=True)

def remove_unused_materials_from_mesh_object(objectToClean):
    """Attempts to identify all materials in use, and then will remove the unused materials"""
    materialIndicesInUse = []

    for i in range(len(objectToClean.data.polygons)):
        poly = objectToClean.data.polygons[i]
        materialIndicesInUse.append(poly.material_index)

    materialIndicesInUse.sort()

    numMaterials = len(objectToClean.data.materials)
    j = 0
    for i in range(numMaterials):
        if i not in materialIndicesInUse:
            objectToClean.data.materials.pop(index=j, update_data=True)
            j -= 1
        j += 1

def create_blender_materials_from_list(materialList, texturePaths):
    """Takes a list of RSEMaterialDefinition and creates a list of blender materials"""
    blenderMaterials = []

    for materialSpec in materialList:
        newMaterial = create_material_from_RSE_specification(materialSpec, texturePaths)
        blenderMaterials.append(newMaterial)

    return blenderMaterials


def create_material_from_RSE_specification(materialSpecification, texturePaths):
    """Creates a material from an RSE specification.
    This does ignore some values that don't map well to PBR and don't influence model behaviour much.
    Materials will be more finely tuned in the game engine.

    materialSpecification is an RSEMaterialDefinition as read by RSEModelReader

    gameDataPath is meant to be the Data folder within the games installation
        directory, as that directory structure is used when loading textures"""

    #Create new material
    newMaterial = bpy.data.materials.new(name=materialSpecification.materialName)
    newMaterialBSDFWrap = node_shader_utils.PrincipledBSDFWrapper(newMaterial, is_readonly=False)

    textureName = materialSpecification.textureName
    texToLoad = None

    #Search for texture to load
    for path in texturePaths:
        texToLoad = find_texture(textureName, path)
        #if a texture was found, don't continue searching
        if texToLoad is not None:
            break

    if texToLoad is None:
        print("Failed to find texture: " + str(textureName))
    else:
        pass
        #print("Final texture to load: " + str(texToLoad))

    #TODO: Refactor texture loading, expand to support image sequences
    if texToLoad is not None:
        # Texture loading code adapted from https://stackoverflow.com/q/19076062
        # Load the image
        texImage = bpy.data.images.load(texToLoad)
        # Create texture from image
        # Add texture slot for color texture
        #textureSlot = newMaterial.texture_paint_slots.add()

        if materialSpecification.alphaMethod != RSEAlphaMethod.SAM_Opaque:
            newMaterialBSDFWrap.base_color_texture.use_alpha = True
            #textureSlot.use_map_alpha = True
            #textureSlot.alpha_factor = materialSpecification.opacity
        newMaterialBSDFWrap.base_color_texture.image = texImage
        newMaterialBSDFWrap.base_color_texture.texcoords = 'UV'

    materialBlendMode = "opaque"
    if materialSpecification.alphaMethod == RSEAlphaMethod.SAM_MethodLookup:
        if materialSpecification.CXPMaterialProperties is not None:
            materialBlendMode = materialSpecification.CXPMaterialProperties.blendMode


    if materialBlendMode != "opaque":
        #TODO: Enable proper translucency in blender 2.8
        #TODO: Toggle shadows in blender 2.8
        #newMaterial.use_transparency = True
        #Blenders material transparency method is different to how masked alpha would work in a game engine,
        # this still provides alpha blending, but if you use Z method the transparent part of the surface
        # still has specular properties. In this instance, MASK provides expected results
        #On further reflection, this might actually be desired. Left the comments here and other parameters which can be tweaked as more areas are tested. This also has the benefit of allowing transparency to work in Rendered mode.
        #newMaterial.transparency_method = 'MASK'
        if materialBlendMode == "colorkey":
            #TODO: Setup a node in material to mask based on the colorkey color
            newMaterial.blend_method = 'CLIP'
        else:
            newMaterial.blend_method = 'BLEND'
        #newMaterial.specular_alpha = 0.0

        #disable shadowing on translucent materials, as unexpected results occur otherwise
        #TODO: Reenable the options for toggling shadows when API is better documented
        #newMaterialBSDFWrap.use_cast_shadows = False
        #newMaterialBSDFWrap.use_shadows = False

        if texToLoad is not None:
            newMaterialBSDFWrap.transmission = 0.0
        else:
            #TODO: Check that opacity is not used when alphaMethod == 1 or SAM_Opaque
            newMaterialBSDFWrap.transmission = materialSpecification.opacity

    # TODO: work out if materialSpecification.ambient should be averaged and applied
    # to newMaterial.ambient, or if it's for the lighting model that might be
    # specified in materialSpecification.unknown2
    newMaterial.diffuse_color = materialSpecification.diffuseColorFloat[0:3]  # change color
    newMaterial.specular_color = materialSpecification.specularColorFloat[0:3]

    newMaterialBSDFWrap.specular = materialSpecification.specularLevel
    newMaterialBSDFWrap.roughness = 1 - materialSpecification.specularLevel
    #newMaterial.use_vertex_color_light = True


    return newMaterial

def import_renderable_array(renderable, blenderMaterials, meshNamePrefix=""):
    """Creates a mesh in blender from a RenderableArray object"""
    meshName = ""
    if renderable.materialIndex == R6Constants.UINT_MAX:
        meshName = meshNamePrefix + str(renderable.materialIndex) + "_renderable"
    else:
        meshName = meshNamePrefix + blenderMaterials[renderable.materialIndex].name + "_renderable"
    newMesh, meshObj = create_blender_mesh_object(meshName)

    for vert in renderable.vertices:
        vert[0] = vert[0] * -1

    add_mesh_geometry(newMesh, renderable.vertices, renderable.triangleIndices)

    ########################################
    # Copy to bmesh from mesh
    ########################################
    newBmesh = bmesh.new()
    newBmesh.from_mesh(newMesh)
    color_layer = newBmesh.loops.layers.color.new("color")
    uv_layer = newBmesh.loops.layers.uv.verify()

    ########################################
    # Apply Vertex Colors if they exist
    ########################################
    if renderable.vertexColors is not None:
        # Cobbled together from : https://blender.stackexchange.com/a/60730
        for face_index, face in enumerate(newBmesh.faces):
            if face is None:
                continue
            sourceTriangleIndices = renderable.triangleIndices[face_index]
            for vert_index, vert in enumerate(face.loops):
                importedColor = renderable.vertexColors[sourceTriangleIndices[vert_index]]
                vert[color_layer] = importedColor

    ########################################
    # Apply UV Mapping
    ########################################
    if renderable.UVs is not None:
        # Cobbled together from https://docs.blender.org/api/blender_python_api_2_67_release/bmesh.html#customdata-access
        for face_index, face in enumerate(newBmesh.faces):
            if face is None:
                continue
            sourceTriangleIndices = renderable.triangleIndices[face_index]
            for vert_index, vert in enumerate(face.loops):
                importedUV = renderable.UVs[sourceTriangleIndices[vert_index]]
                if math.isnan(importedUV[0]):
                    vert[uv_layer].uv.x = 0.0
                else:
                    vert[uv_layer].uv.x = importedUV[0]
                # This coord seems to be inverted, this seems to look correct.
                if math.isnan(importedUV[1]):
                    vert[uv_layer].uv.y = 0.0
                else:
                    vert[uv_layer].uv.y = importedUV[1] * -1


    #Reverse face winding, to ensure backface culling is correct
    bmesh.ops.reverse_faces(newBmesh, faces=newBmesh.faces)

    #TODO: Import normals

    ########################################
    # Copy from bmesh back to mesh
    ########################################

    newBmesh.to_mesh(newMesh)
    newBmesh.free()
    newMesh.update(calc_edges=True)

    ########################################
    # Apply Material per face
    ########################################
    #Do not assign a material if index is UINT_MAX
    if renderable.materialIndex != R6Constants.UINT_MAX:
        meshObj.data.materials.append(blenderMaterials[renderable.materialIndex])
        for i in range(len(newMesh.polygons)):
            poly = newMesh.polygons[i]
            poly.material_index = 0

    return meshObj

def create_objects_from_R6GeometryObject(geometryObject, blenderMaterials):
    """ Generates blender objects from an R6GeometryObject and adds appropriate tags """
    geoObjectName = geometryObject.nameString
    geoBlendObj = create_blender_blank_object(geoObjectName)

    #fix up rotation
    geoBlendObj.rotation_euler = (math.radians(90), 0, 0)

    for index, mesh in enumerate(geometryObject.meshes):
        #TODO: Add GeometryFlags as custom properties, as well as unknown vars
        meshName =  geometryObject.nameString + "_" + mesh.nameString + "_idx" + str(index)
        meshObj = create_blender_blank_object(meshName)
        meshObj.parent = geoBlendObj

        for flag in mesh.geometryFlagsEvaluated:
            meshObj[flag] = mesh.geometryFlagsEvaluated[flag]

        renderables = geometryObject.generate_renderable_arrays_for_mesh(mesh)
        renderable_prefix = meshName + "_"
        for renderable in renderables:
            renderableMesh = import_renderable_array(renderable, blenderMaterials, renderable_prefix)
            renderableMesh.parent = meshObj

def create_objects_from_RSMAPGeometryObject(geometryObject, blenderMaterials):
    """Creates all meshes associated with an RSMAPGeometryObject"""
    geoObjName = geometryObject.nameString

    geoObjectParentObject = create_blender_blank_object(geoObjName)

    #fix up rotation
    geoObjectParentObject.rotation_euler = (math.radians(90),0,0)

    subObjects = []
    for idx, facegroup in enumerate(geometryObject.geometryData.faceGroups):
        faceGroupPrefix = geoObjName + "_idx" + str(idx) + "_mat" + str(facegroup.materialIndex)
        renderable = geometryObject.geometryData.generate_renderable_array_for_facegroup(facegroup)
        subObject = import_renderable_array(renderable, blenderMaterials, faceGroupPrefix)
        subObject.parent = geoObjectParentObject
        subObjects.append(subObject)

    collisionName = geoObjName + "_collision"
    collisionData = geometryObject.geometryData.collisionInformation
    for i, collMesh in enumerate(collisionData.collisionMeshDefinitions):
        if collMesh.geometryFlagsEvaluated["GF_INVISIBLE"] is True:
            #Do not process invalid and unused meshes
            continue
        subCollisionName = collisionName + "_idx" + str(i)
        renderable = collisionData.generate_renderable_array_for_collisionmesh(collMesh, geometryObject.geometryData)
        subObject = import_renderable_array(renderable, blenderMaterials, subCollisionName)
        subObject.parent = geoObjectParentObject
        subObjects.append(subObject)

        for flag in collMesh.geometryFlagsEvaluated:
            subObject[flag] = collMesh.geometryFlagsEvaluated[flag]

        if collMesh.geometryFlagsEvaluated["GF_INVISIBLE"] is True:
            # Pretty sure GF_INVISIBLE on collision geometry means ignored
            subObject.hide_viewport = True
            subObject.hide_render = True
            subObject.hide_select = True
    #collisionObj = create_mesh_from_RSMAPCollisionInformation(geometryObject.geometryData, blenderMaterials, collisionName)
    #collisionObj.parent = geoObjectParentObject
