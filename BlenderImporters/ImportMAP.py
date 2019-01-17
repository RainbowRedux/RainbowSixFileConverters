import random
import os
import sys
from math import radians
import math

import bpy
import bmesh
import mathutils

sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders import R6Constants
from RainbowFileReaders.R6Constants import RSEGameVersions
from RainbowFileReaders.MathHelpers import normalize_color, pad_color

from BlenderImporters.ImportSOB import create_objects_from_R6GeometryObject
from BlenderImporters import BlenderUtils

def create_mesh_from_RSMAPCollisionInformation(geometryObjectDefinition, blenderMaterials, name):

    collisionObjectDefinition = geometryObjectDefinition.collisionInformation

    geoObjBlendMeshMaster, geoObjBlendObjectMaster = BlenderUtils.create_blender_mesh_object(name + "_TEMPMASTER")

    geoObjectParentObject = BlenderUtils.create_blender_blank_object(name)

    #fix up rotation
    #geoObjectParentObject.rotation_euler = (radians(90),0,0)

    ########################################
    # Conform faces to desired data structure
    ########################################
    faces = []
    for face in collisionObjectDefinition.faces:
        faces.append(face.vertexIndices)

    #reverse the scaling on the z axis, to correct LHS <-> RHS conversion
    #this must be done here to not change the face winding which would interfere with backface culling
    verts = geometryObjectDefinition.vertices.copy()
    for vert in collisionObjectDefinition.vertices:
        vert[0] = vert[0] * -1

    BlenderUtils.add_mesh_geometry(geoObjBlendMeshMaster, verts, faces)

    numTotalFaces = collisionObjectDefinition.faceCount
    numCreatedFaces = len(geoObjBlendObjectMaster.data.polygons)

    if numCreatedFaces != numTotalFaces:
        print("Not enough faces created")
        raise ValueError("Not enough faces created")

    geoObjBlendObjectMaster.parent = geoObjectParentObject

    ########################################
    # Create sub meshes
    ########################################
    createdSubMeshes = []

    #Split Meshes
    for index, meshdef in enumerate(collisionObjectDefinition.collisionMeshDefinitions):
        newObjectName = name + "_" + meshdef.nameString + "_idx" + str(index)
        uniqueFaceIndices = list(set(meshdef.faceIndices))

        newSubBlendObject = BlenderUtils.clone_mesh_object_with_specified_faces(newObjectName, uniqueFaceIndices, geoObjBlendObjectMaster)

        if newSubBlendObject is not None:
            newSubBlendObject.parent = geoObjectParentObject
            createdSubMeshes.append(newSubBlendObject)

            for flag in meshdef.geometryFlagsEvaluated:
                newSubBlendObject[flag] = meshdef.geometryFlagsEvaluated[flag]

            if meshdef.geometryFlagsEvaluated["GF_INVISIBLE"] is True:
                # Pretty sure GF_INVISIBLE on collision geometry means ignored
                newSubBlendObject.hide_viewport = True
                newSubBlendObject.hide_render = True
                newSubBlendObject.hide_select = True


    bpy.data.meshes.remove(geoObjBlendMeshMaster)

    return geoObjectParentObject

def import_face_group_as_mesh(faceGroup, vertices, blenderMaterials, name):
    geoObjBlendMesh, geoObjBlendObject = BlenderUtils.create_blender_mesh_object(name)

    faces = []
    #these faces appear to be stored as CCW winding, blender expects CW winding, can flip set of params on import, or flip all after import
    for face in faceGroup.faceVertexIndices:
        faces.append(face)
    BlenderUtils.add_mesh_geometry(geoObjBlendMesh, vertices, faces)

    numTotalFaces = faceGroup.faceCount
    numCreatedFaces = len(geoObjBlendObject.data.polygons)

    if numCreatedFaces != numTotalFaces:
        raise ValueError("Not enough faces created")

    ########################################
    # Copy to bmesh from mesh
    ########################################

    newBmesh = bmesh.new()
    newBmesh.from_mesh(geoObjBlendMesh)
    color_layer = newBmesh.loops.layers.color.new("color")
    uv_layer = newBmesh.loops.layers.uv.verify()
    #newBmesh.faces.layers.tex.verify()  # currently blender needs both layers.

    ########################################
    # Apply Vertex Colors
    ########################################

    # Cobbled together from : https://blender.stackexchange.com/a/60730
    for face_index, face in enumerate(newBmesh.faces):
        if face is None:
            continue
        importedParamIndices = faceGroup.faceVertexParamIndices[face_index]
        for vert_index, vert in enumerate(face.loops):
            importedColor = faceGroup.vertexParams.colors[importedParamIndices[vert_index]]
            importedColor = normalize_color(importedColor)
            vert[color_layer] = pad_color(importedColor)

    ########################################
    # Apply UV Mapping
    ########################################
    # Cobbled together from https://docs.blender.org/api/blender_python_api_2_67_release/bmesh.html#customdata-access
    for face_index, face in enumerate(newBmesh.faces):
        if face is None:
            continue
        importedParamIndices = faceGroup.faceVertexParamIndices[face_index]
        for vert_index, vert in enumerate(face.loops):
            importedUV = faceGroup.vertexParams.UVs[importedParamIndices[vert_index]]
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

    ########################################
    # Copy from bmesh back to mesh
    ########################################

    newBmesh.to_mesh(geoObjBlendMesh)
    newBmesh.free()
    geoObjBlendMesh.update(calc_edges=True)

    #Map materials to faces
    #TODO: Also remove the reduced material index mapping code which is overcomplicating this block
    materialMapping = {}
    reducedMaterials = []
    for i in range(len(geoObjBlendMesh.polygons)):
        poly = geoObjBlendMesh.polygons[i]
        materialIndex = faceGroup.materialIndex
        #Do not assign a material if index is UINT_MAX
        if materialIndex == R6Constants.UINT_MAX:
            continue

        if materialIndex not in materialMapping:
            reducedMaterials.append(blenderMaterials[materialIndex])
            geoObjBlendObject.data.materials.append(blenderMaterials[materialIndex])
            materialMapping[materialIndex] = len(reducedMaterials) - 1

        poly.material_index = materialMapping[materialIndex]

    return geoObjBlendObject

def create_objects_from_RSMAPGeometryObject(geometryObject, blenderMaterials):
    geoObjName = geometryObject.nameString

    geoObjectParentObject = BlenderUtils.create_blender_blank_object(geoObjName)

    #fix up rotation
    geoObjectParentObject.rotation_euler = (radians(90),0,0)

    for vert in geometryObject.geometryData.vertices:
        vert[0] = vert[0] * -1

    subObjects = []
    for idx, facegroup in enumerate(geometryObject.geometryData.faceGroups):
        faceGroupName = geoObjName + "_idx" + str(idx) + "_mat" + str(facegroup.materialIndex)
        subObject = import_face_group_as_mesh(facegroup, geometryObject.geometryData.vertices, blenderMaterials, faceGroupName)
        subObject.parent = geoObjectParentObject
        subObjects.append(subObject)

    collisionName = geoObjName + "_collision"
    collisionObj = create_mesh_from_RSMAPCollisionInformation(geometryObject.geometryData, blenderMaterials, collisionName)
    collisionObj.parent = geoObjectParentObject

def create_spotlight_from_r6_light_specification(lightSpec, name):
    #https://stackoverflow.com/a/17355744
    lamp_data = None
    lamp_data = bpy.data.lights.new(name=lightSpec.nameString + "_pointdata", type='POINT')
    # Create new object with our lamp datablock
    lamp_object = bpy.data.objects.new(name=name, object_data=lamp_data)
    # Link lamp object to the scene so it'll appear in this scene
    bpy.context.scene.collection.objects.link(lamp_object)
    # And finally select it make active
    lamp_object.select_set(True)
    bpy.context.view_layer.objects.active = lamp_object

    # Place lamp to a specified location
    position = lightSpec.position
    position[0] *= -1.0
    lamp_object.location = position


    #do rotation matrix work
    matRow1 = lightSpec.transformMatrix[0:3]
    matRow2 = lightSpec.transformMatrix[3:6]
    matRow3 = lightSpec.transformMatrix[6:9]
    transformMatrix = mathutils.Matrix((matRow1, matRow2, matRow3))
    lamp_object.rotation_euler = transformMatrix.to_euler()
    importedQuat = transformMatrix.to_quaternion()

    #correct the incorrect rotation due to coordinate system conversion
    coordSystemConversionQuat = mathutils.Euler((radians(-90), 0, 0)).to_quaternion()
    finalQuat = importedQuat @ coordSystemConversionQuat
    lamp_object.rotation_euler = finalQuat.to_euler()



    color = []
    for color_el in lightSpec.color:
        color.append(color_el / 255.0)
    lamp_data.color = color

    lamp_data.falloff_type = 'INVERSE_COEFFICIENTS'
    lamp_data.constant_coefficient = lightSpec.constantAttenuation
    lamp_data.linear_coefficient = lightSpec.linearAttenuation
    lamp_data.quadratic_coefficient = lightSpec.quadraticAttenuation

    #TODO: Fix these approximations
    lamp_data.energy = lightSpec.energy * 25
    lamp_data.shadow_soft_size = lightSpec.falloff
    #lamp_data.use_custom_distance = True
    #lamp_data.distance = lightSpec.energy
    lamp_data.use_shadow = False


    #lamp_data.specular_factor = lightSpec.unknown7

    return lamp_object

def import_r6_lights(lightlist):
    lightGroup = bpy.data.objects.new("LightGroup", None)
    lightGroup.location = (0,0,0)
    lightGroup.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(lightGroup)
    lightGroup.rotation_euler = (radians(90),0,0)

    for idx, light in enumerate(lightlist.lights):
        name = light.nameString + "_idx" + str(idx)
        newLamp = create_spotlight_from_r6_light_specification(light, name)
        newLamp.parent = lightGroup

def create_spotlight_from_rs_light_specification(lightSpec, name):
    #https://stackoverflow.com/a/17355744
    lamp_data = None
    lamp_data = bpy.data.lights.new(name=lightSpec.nameString + "_pointdata", type='POINT')
    # Create new object with our lamp datablock
    lamp_object = bpy.data.objects.new(name=name, object_data=lamp_data)
    # Link lamp object to the scene so it'll appear in this scene
    bpy.context.scene.collection.objects.link(lamp_object)
    # And finally select it make active
    lamp_object.select_set(True)
    bpy.context.view_layer.objects.active = lamp_object

    # Place lamp to a specified location
    position = lightSpec.position
    position[0] *= -1.0
    lamp_object.location = position

    #correct the incorrect rotation due to coordinate system conversion
    # coordSystemConversionQuat = mathutils.Euler((radians(-90), 0, 0)).to_quaternion()
    # finalQuat = importedQuat @ coordSystemConversionQuat
    # lamp_object.rotation_euler = finalQuat.to_euler()

    lamp_data.color = lightSpec.diffuseColor[:3]

    lamp_data.falloff_type = 'INVERSE_COEFFICIENTS'
    lamp_data.constant_coefficient = lightSpec.constantAttenuation
    lamp_data.linear_coefficient = lightSpec.linearAttenuation
    lamp_data.quadratic_coefficient = lightSpec.quadraticAttenuation

    #TODO: Fix these approximations
    lamp_data.energy = lightSpec.energy * 25
    lamp_data.shadow_soft_size = lightSpec.falloff
    #lamp_data.use_custom_distance = True
    #lamp_data.distance = lightSpec.energy
    lamp_data.use_shadow = False


    #lamp_data.specular_factor = lightSpec.unknown7

    return lamp_object

def import_rs_lights(dmpLightFile):
    lightGroup = bpy.data.objects.new("LightGroup", None)
    lightGroup.location = (0,0,0)
    lightGroup.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(lightGroup)
    lightGroup.rotation_euler = (radians(90),0,0)

    for idx, light in enumerate(dmpLightFile.lights):
        name = light.nameString + "_idx" + str(idx)
        newLamp = create_spotlight_from_rs_light_specification(light, name)
        newLamp.parent = lightGroup

def import_MAP_to_scene(filename):
    if filename.endswith("obstacletest.map"):
        #I believe this is an early test map that was shipped by accident.
        # It's data structures are not consistent with the rest of the map files
        # and it is not used anywhere so it is safe to skip
        print("Skipping test map: " + filename)
        return False
    MAPObject = MAPLevelReader.MAPLevelFile()
    MAPObject.read_file(filename)

    BlenderUtils.setup_blank_scene()

    print("")
    print("Beginning import")

    texturePaths = R6Settings.get_relevant_texture_paths(filename)

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(MAPObject.materials, texturePaths)

    if MAPObject.gameVersion == RSEGameVersions.RAINBOW_SIX:
        for geoObj in MAPObject.geometryObjects:
            create_objects_from_R6GeometryObject(geoObj, blenderMaterials)
    else:
        for geoObj in MAPObject.geometryObjects:
            create_objects_from_RSMAPGeometryObject(geoObj, blenderMaterials)

    if MAPObject.gameVersion == RSEGameVersions.RAINBOW_SIX:
        import_r6_lights(MAPObject.lightList)
    else:
        import_rs_lights(MAPObject.dmpLights)

    print("Import Map Succeeded")
    return True


def save_blend_scene(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)

def export_fbx_scene(path):
    bpy.ops.export_scene.fbx(filepath=path, path_mode='RELATIVE')

def import_map_and_save(path):
    inPath = os.path.abspath(path)
    outBlendPath = inPath + ".blend"
    outFBXPath = inPath + ".fbx"
    importSuccess = import_MAP_to_scene(inPath)
    if importSuccess:
        save_blend_scene(outBlendPath)
        export_fbx_scene(outFBXPath)


if __name__ == "__main__":
    import_MAP_to_scene(sys.argv[-1])
