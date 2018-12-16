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
from RainbowFileReaders.MathHelpers import normalize_color, sanitize_float

from BlenderImporters import BlenderUtils

errorCount = 0
errorList = []

def create_mesh_from_RSGeometryObject(geometryObject, blenderMaterials):
    name = geometryObject.nameString

    geoObjBlendMesh, geoObjBlendObject = BlenderUtils.create_blender_mesh_object(name)
    #attach_materials_to_blender_object(geoObjBlendObject, blenderMaterials)

    #fix up rotation
    geoObjBlendObject.rotation_euler = (radians(90),0,0)
    #rot1 = mathutils.Euler((0, 0, radians(-90))).to_quaternion()
    #rot2 = mathutils.Euler((0, radians(90), 0)).to_quaternion()
    #finalRot = rot2*rot1
    #eulerRot = finalRot.to_euler()
    #geoObjBlendObject.rotation_euler = eulerRot

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

    #TODO: Modify the following parts to be in separate functions so they can be used for other mesh formats

    ########################################
    # Copy to bmesh from mesh
    ########################################

    newBmesh = bmesh.new()
    newBmesh.from_mesh(geoObjBlendMesh)
    color_layer = newBmesh.loops.layers.color.new("color")
    uv_layer = newBmesh.loops.layers.uv.verify()
    newBmesh.faces.layers.tex.verify()  # currently blender needs both layers.

    print("Number of faces: " + str(len(newBmesh.faces)))

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
    
    newBmesh.to_mesh(geoObjBlendMesh)
    newBmesh.free()
    geoObjBlendMesh.update(calc_edges=True)

    ########################################
    # Apply Materials per face
    ########################################
    materialMapping = {}
    reducedMaterials = []
    #TODO: Remove the reduced materials mapping which is just overcomplicating things, there is a cleanup pass at the end anyway
    for i in range(len(geoObjBlendMesh.polygons)):
        poly = geoObjBlendMesh.polygons[i]
        faceProperties = geometryObject.faces[i]
        #Do not assign a material if index is UINT_MAX
        if faceProperties.materialIndex == R6Constants.UINT_MAX:
            continue

        if faceProperties.materialIndex not in materialMapping:
            reducedMaterials.append(blenderMaterials[faceProperties.materialIndex])
            geoObjBlendObject.data.materials.append(blenderMaterials[faceProperties.materialIndex])
            materialMapping[faceProperties.materialIndex] = len(reducedMaterials) - 1
        
        poly.material_index = materialMapping[faceProperties.materialIndex]

    # TODO: Import normals

    createdSubMeshes = []

    #Split Meshes
    for index, rsemesh in enumerate(geometryObject.meshes):
        newObjectName = rsemesh.nameString + "_idx_" + str(index) + "_geo_" + geometryObject.nameString
        uniqueFaceIndicies = list(set(rsemesh.faceIndices))
        
        newSubBlendObject = BlenderUtils.clone_mesh_object_with_specified_faces(newObjectName, uniqueFaceIndicies, geoObjBlendObject)

        if newSubBlendObject is not None:
            newSubBlendObject.parent = geoObjBlendObject
            createdSubMeshes.append(newSubBlendObject)
            #newSubBlendObject.rotation_euler = (radians(90),0,0)


    #clean used materials from each object
    objectsToCleanMaterialsFrom = createdSubMeshes.copy()
    objectsToCleanMaterialsFrom.append( geoObjBlendObject)
    for objectToClean in objectsToCleanMaterialsFrom:
        BlenderUtils.remove_unused_materials_from_mesh_object(objectToClean)


    #delete original master mesh data
    bpy.context.scene.objects.active = geoObjBlendObject
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete(type='FACE') # will be acted on.
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Number of mesh split errors: " + str(errorCount))
    for err in errorList:
        print(err)


def import_SOB_to_scene(filename):
    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_file(filename)
    filepath = os.path.dirname(filename)
    
    print("")
    print("Beginning import")

    print("File is in directory: " + filepath)
    gameDataPath = os.path.split(filepath)[0]
    print("Assuming gamepath is: " + gameDataPath)

    #TODO Add step for converting from LHS to RHS, and probably rotating to having another axis as the up axis

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(SOBObject.materials, filepath, gameDataPath)

    for geoObj in SOBObject.geometryObjects:
        create_mesh_from_RSGeometryObject(geoObj, blenderMaterials)

    print("Success")


if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene(sys.argv[-1])