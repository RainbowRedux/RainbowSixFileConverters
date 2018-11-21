import random
import os
import sys

import bpy
import bmesh

sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders import R6Constants
from RainbowFileReaders.R6Constants import UINT_MAX, RSEGameVersions
from RainbowFileReaders.MathHelpers import normalize_color, sanitize_float

from BlenderImporters import ImportSOB
from BlenderImporters.ImportSOB import create_blender_materials_from_list, create_mesh_from_RSGeometryObject


def import_MAP_to_scene(filename):
    MAPObject = MAPLevelReader.MAPLevelFile()
    MAPObject.read_file(filename)
    filepath = os.path.dirname(filename)
    
    print("")
    print("Beginning import")

    print("File is in directory: " + filepath)
    gameDataPath = os.path.split(filepath)[0]
    gameDataPath = os.path.split(gameDataPath)[0]
    print("Assuming gamepath is: " + gameDataPath)

    blenderMaterials = create_blender_materials_from_list(MAPObject.materials, filepath, gameDataPath)

    if MAPObject.gameVersion == RSEGameVersions.RAINBOW_SIX:
        for geoObj in MAPObject.geometryObjects:
            create_mesh_from_RSGeometryObject(geoObj, blenderMaterials)
    else:
        print("No import method implemented for this version of geometry yet")

    print("Success")

#"E:\Dropbox\Development\Rainbow\Data\R6GOG\data\map\m01\M01.map"
import_MAP_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\map\\m01\\M01.map")