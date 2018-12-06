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
from RainbowFileReaders.R6Constants import UINT_MAX, RSEGameVersions, RSELightTypes
from RainbowFileReaders.MathHelpers import normalize_color, sanitize_float

from BlenderImporters import ImportSOB
from BlenderImporters.ImportSOB import create_mesh_from_RSGeometryObject
from BlenderImporters import BlenderUtils

def create_mesh_from_RSMAPGeometryObject(geometryObject, blenderMaterials):
    name = geometryObject.nameString

    geoObjBlendMesh, geoObjBlendObject = BlenderUtils.create_blender_mesh_object(name)
    #attach_materials_to_blender_object(geoObjBlendObject, blenderMaterials)

    #fix up rotation
    geoObjBlendObject.rotation_euler = (radians(90),0,0)

    ########################################
    # Conform faces to desired data structure
    ########################################
    faces = []
    for face in geometryObject.faces:
        faces.append(face.vertexIndices)

    #reverse the scaling on the z axis, to correct LHS <-> RHS conversion
    #this must be done here to not change the face winding which would interfere with backface culling
    for vert in geometryObject.vertices:
        vert[0] = vert[0] * -1

    BlenderUtils.add_mesh_geometry(geoObjBlendMesh, geometryObject.vertices, faces)

    numTotalFaces = geometryObject.faceCount
    numCreatedFaces = len(geoObjBlendObject.data.polygons)

    if numCreatedFaces != numTotalFaces:
        raise ValueError("Not enough faces created")
    pass

def create_spotlight_from_light_specification(lightSpec):
    #https://stackoverflow.com/a/17355744
    lamp_data = None
    if math.isclose(lightSpec.falloff, 0.0):
        print("point")
        lamp_data = bpy.data.lamps.new(name=lightSpec.nameString + "_pointdata", type='POINT')
    else:
        print("spot")
        lamp_data = bpy.data.lamps.new(name=lightSpec.nameString + "_spotdata", type='SPOT')
        lamp_data.spot_size = radians(lightSpec.falloff)
        lamp_data.show_cone = True
    # Create new object with our lamp datablock
    lamp_object = bpy.data.objects.new(name=lightSpec.nameString, object_data=lamp_data)
    # Link lamp object to the scene so it'll appear in this scene
    bpy.context.scene.objects.link(lamp_object)
    # And finally select it make active
    lamp_object.select = True
    bpy.context.scene.objects.active = lamp_object

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
    finalQuat = importedQuat * coordSystemConversionQuat
    lamp_object.rotation_euler = finalQuat.to_euler()

    

    color = []
    for color_el in lightSpec.color:
        color.append(color_el / 255.0)
    lamp_data.color = color

    lamp_data.falloff_type = 'INVERSE_COEFFICIENTS'
    lamp_data.constant_coefficient = lightSpec.constantAttenuation
    lamp_data.linear_coefficient = lightSpec.linearAttenuation
    lamp_data.quadratic_coefficient = lightSpec.quadraticAttenuation

    lamp_data.energy = 1.0
    lamp_data.distance = lightSpec.energy
    lamp_data.use_sphere = True
    lamp_data.shadow_method = 'NOSHADOW'


    #lamp_data.specular_factor = lightSpec.unknown7

    return lamp_object

    pass


def import_lights(lightlist):
    lightGroup = bpy.data.objects.new("LightGroup", None)
    lightGroup.location = (0,0,0)
    lightGroup.show_name = True
    # Link object to scene
    bpy.context.scene.objects.link(lightGroup)
    lightGroup.rotation_euler = (radians(90),0,0)

    for light in lightlist.lights:
        if light.type == RSELightTypes.SPOTLIGHT:
            newLamp = create_spotlight_from_light_specification(light)
            newLamp.parent = lightGroup
        else:
            print("Skipping light: " + light.nameString)

def import_MAP_to_scene(filename):
    MAPObject = MAPLevelReader.MAPLevelFile()
    MAPObject.read_file(filename)
    filepath = os.path.dirname(filename)
    
    BlenderUtils.setup_blank_scene()

    print("")
    print("Beginning import")

    print("File is in directory: " + filepath)
    gameDataPath = os.path.split(filepath)[0]
    gameDataPath = os.path.split(gameDataPath)[0]
    print("Assuming gamepath is: " + gameDataPath)

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(MAPObject.materials, filepath, gameDataPath)

    if MAPObject.gameVersion == RSEGameVersions.RAINBOW_SIX:
        for geoObj in MAPObject.geometryObjects:
            create_mesh_from_RSGeometryObject(geoObj, blenderMaterials)
    else:
        for geoObj in MAPObject.geometryObjects:
            pass
            #create_mesh_from_RSMAPGeometryObject(geoObj, blenderMaterials)
        print("No import method implemented for this version of geometry yet")

    import_lights(MAPObject.lightList)

    print("Success")

#"E:\Dropbox\Development\Rainbow\Data\R6GOG\data\map\m01\M01.map"
#import_MAP_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\map\\m07\\m7.map")
import_MAP_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\map\\m01\\M01.map")
#"E:\Dropbox\Development\Rainbow\Data\RSDemo\data\map\rm01\rm01.map"
#import_MAP_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\RSDemo\\data\\map\\rm01\\rm01.map")
#import_MAP_to_scene("/Users/philipedwards/Dropbox/Development/Rainbow/Data/R6GOG/data/map/m01/M01.map")
#import_MAP_to_scene("/Users/philipedwards/Dropbox/Development/Rainbow/Data/R6GOG/data/map/m07/m7.map")
#import_MAP_to_scene(sys.argv[-1])