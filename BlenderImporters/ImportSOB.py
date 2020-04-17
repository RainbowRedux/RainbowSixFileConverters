"""
Functions related to import SOB files into a blender scene
"""

import sys
import logging

sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import R6Settings

from BlenderImporters import BlenderUtils
from BlenderImporters.BlenderUtils import create_objects_from_R6GeometryObject

log = logging.getLogger(__name__)

def import_SOB_to_scene(filename: str):
    """Opens SOB file and imports all relevant information"""
    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_file(filename)

    log.info("Beginning import")

    texturePaths = R6Settings.get_relevant_global_texture_paths(filename)

    blenderMaterials = BlenderUtils.create_blender_materials_from_list(SOBObject.materials, texturePaths)

    for geoObj in SOBObject.geometryObjects:
        create_objects_from_R6GeometryObject(geoObj, blenderMaterials)

    log.info("Success")


if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene(sys.argv[-1])
