"""
Functions related to import SOB files into a blender scene
"""
import sys
from math import radians

import bpy
import bmesh

sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import R6Settings

from BlenderImporters import BlenderUtils
from BlenderImporters.BlenderUtils import import_renderable_array

errorCount = 0
errorList = []

def import_SOB_to_scene(filename):
    """Opens SOB file and imports all relevant information"""
    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_file(filename)

    print("")
    print("Beginning import")

    texturePaths = R6Settings.get_relevant_texture_paths(filename)

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(SOBObject.materials, texturePaths)

    for geoObj in SOBObject.geometryObjects:
        geoObjectName = geoObj.nameString
        geoBlendObj = BlenderUtils.create_blender_blank_object(geoObjectName)
        geoBlendObj.rotation_euler = (radians(90), 0, 0)
        for index, mesh in enumerate(geoObj.meshes):
            meshName =  geoObj.nameString + "_" + mesh.nameString + "_idx" + str(index)
            meshObj = BlenderUtils.create_blender_blank_object(meshName)
            meshObj.parent = geoBlendObj
            renderables = geoObj.generate_renderable_array_for_mesh(mesh)
            for renderable in renderables:
                renderableMesh = import_renderable_array(renderable, blenderMaterials)
                renderableMesh.parent = meshObj

    print("Success")


if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene(sys.argv[-1])
