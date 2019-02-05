"""
Functions to import MAP files into blender
"""
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

from BlenderImporters import BlenderUtils
from BlenderImporters.BlenderUtils import import_renderable_array, create_objects_from_R6GeometryObject, create_objects_from_RSMAPGeometryObject

def create_mesh_from_RSMAPCollisionInformation(geometryObjectDefinition, blenderMaterials, name):
    """Creates appropriate meshes off of RSMAPCollisionInformation objects"""
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

def create_spotlight_from_r6_light_specification(lightSpec, name):
    """Create a spotlight from a rainbow six light specification"""
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
    """Import all lights from a rainbow six map"""
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
    """Create a spotlight from a rogue spear light specification"""
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
    """Import all lights from a rogue spear DMP file"""
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
    """Imports a given map to the blender scene.
    Skips files named obstacletest.map since its an invalid test file on original rainbow six installations"""
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
    """Saves the scene to a .blend file"""
    bpy.ops.wm.save_as_mainfile(filepath=path)

def export_fbx_scene(path):
    """exports the scene to a .fbx file"""
    bpy.ops.export_scene.fbx(filepath=path, path_mode='RELATIVE')

def import_map_and_save(path):
    """Wrapper method to import a map to scene, save and export"""
    inPath = os.path.abspath(path)
    outBlendPath = inPath + ".blend"
    outFBXPath = inPath + ".fbx"
    importSuccess = import_MAP_to_scene(inPath)
    if importSuccess:
        save_blend_scene(outBlendPath)
        export_fbx_scene(outFBXPath)


if __name__ == "__main__":
    import_MAP_to_scene(sys.argv[-1])
