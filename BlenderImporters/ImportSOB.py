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
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders import R6Constants
from RainbowFileReaders.R6Constants import UINT_MAX
from RainbowFileReaders.MathHelpers import normalize_color, sanitize_float, pad_color

from BlenderImporters import BlenderUtils

errorCount = 0
errorList = []

def create_objects_from_R6GeometryObject(geometryObject, blenderMaterials):
    name = geometryObject.nameString

    geoObjBlendMeshMaster, geoObjBlendObjectMaster = BlenderUtils.create_blender_mesh_object(name + "_TEMPMASTER")

    geoObjectParentObject = BlenderUtils.create_blender_blank_object(name)

    #fix up rotation
    geoObjectParentObject.rotation_euler = (radians(90),0,0)
    #rot1 = mathutils.Euler((0, 0, radians(-90))).to_quaternion()
    #rot2 = mathutils.Euler((0, radians(90), 0)).to_quaternion()
    #finalRot = rot2*rot1
    #eulerRot = finalRot.to_euler()
    #geoObjBlendObjectMaster.rotation_euler = eulerRot

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

    BlenderUtils.add_mesh_geometry(geoObjBlendMeshMaster, geometryObject.vertices, faces)

    numTotalFaces = geometryObject.faceCount
    numCreatedFaces = len(geoObjBlendObjectMaster.data.polygons)

    if numCreatedFaces != numTotalFaces:
        raise ValueError("Not enough faces created")

    #TODO: Modify the following parts to be in separate functions so they can be used for other mesh formats

    ########################################
    # Copy to bmesh from mesh
    ########################################

    newBmesh = bmesh.new()
    newBmesh.from_mesh(geoObjBlendMeshMaster)
    color_layer = newBmesh.loops.layers.color.new("color")
    uv_layer = newBmesh.loops.layers.uv.verify()

    ########################################
    # Apply Vertex Colors
    ########################################

    # Cobbled together from : https://blender.stackexchange.com/a/60730
    for face_index, face in enumerate(newBmesh.faces):
        if face is None:
            continue
        importedParamIndices = geometryObject.faces[face_index].paramIndices
        for vert_index, vert in enumerate(face.loops):
            importedColor = geometryObject.vertexParams[importedParamIndices[vert_index]].color
            importedColor = normalize_color(importedColor)
            importedColor = pad_color(importedColor)
            vert[color_layer] = importedColor

    ########################################
    # Apply UV Mapping
    ########################################
    # Cobbled together from https://docs.blender.org/api/blender_python_api_2_67_release/bmesh.html#customdata-access
    for face_index, face in enumerate(newBmesh.faces):
        if face is None:
            continue
        importedParamIndices = geometryObject.faces[face_index].paramIndices
        for vert_index, vert in enumerate(face.loops):
            importedUV = geometryObject.vertexParams[importedParamIndices[vert_index]].UV
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
    
    newBmesh.to_mesh(geoObjBlendMeshMaster)
    newBmesh.free()
    geoObjBlendMeshMaster.update(calc_edges=True)

    ########################################
    # Apply Materials per face
    ########################################
    materialMapping = {}
    reducedMaterials = []
    #TODO: Remove the reduced materials mapping which is just overcomplicating things, there is a cleanup pass at the end anyway
    for i in range(len(geoObjBlendMeshMaster.polygons)):
        poly = geoObjBlendMeshMaster.polygons[i]
        faceProperties = geometryObject.faces[i]
        #Do not assign a material if index is UINT_MAX
        if faceProperties.materialIndex == R6Constants.UINT_MAX:
            continue

        if faceProperties.materialIndex not in materialMapping:
            reducedMaterials.append(blenderMaterials[faceProperties.materialIndex])
            geoObjBlendObjectMaster.data.materials.append(blenderMaterials[faceProperties.materialIndex])
            materialMapping[faceProperties.materialIndex] = len(reducedMaterials) - 1
        
        poly.material_index = materialMapping[faceProperties.materialIndex]

    #TODO: Import normals

    createdSubMeshes = []

    #Split Meshes
    for index, rsemesh in enumerate(geometryObject.meshes):
        newObjectName = geometryObject.nameString + "_" + rsemesh.nameString + "_idx" + str(index)
        uniqueFaceIndicies = list(set(rsemesh.faceIndices))
        
        newSubBlendObject = BlenderUtils.clone_mesh_object_with_specified_faces(newObjectName, uniqueFaceIndicies, geoObjBlendObjectMaster)

        if newSubBlendObject is not None:
            newSubBlendObject.parent = geoObjectParentObject
            createdSubMeshes.append(newSubBlendObject)
            
            for flag in rsemesh.geometryFlagsEvaluated:
                newSubBlendObject[flag] = rsemesh.geometryFlagsEvaluated[flag]


    #clean used materials from each object
    objectsToCleanMaterialsFrom = createdSubMeshes.copy()
    objectsToCleanMaterialsFrom.append( geoObjBlendObjectMaster)
    for objectToClean in objectsToCleanMaterialsFrom:
        BlenderUtils.remove_unused_materials_from_mesh_object(objectToClean)

    bpy.data.meshes.remove(geoObjBlendMeshMaster)
    

def import_SOB_to_scene(filename):
    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_file(filename)
    
    print("")
    print("Beginning import")

    texturePaths = R6Settings.get_relevant_texture_paths(filename)

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(SOBObject.materials, texturePaths)

    for geoObj in SOBObject.geometryObjects:
        create_objects_from_R6GeometryObject(geoObj, blenderMaterials)

    print("Success")


if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene(sys.argv[-1])
