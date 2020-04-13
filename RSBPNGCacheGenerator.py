"""
Loads a game path and then converts all RSBs within to full colour PNGs with the extension .CACHE.PNG
"""

import logging
from os import path

from RainbowFileReaders.CXPMaterialPropertiesReader import load_relevant_cxps, get_cxp_definition
from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.RSBImageReader import RSBImageFile
from RainbowFileReaders.R6Settings import restore_original_texture_name
from FileUtilities.DirectoryUtils import gather_files_in_path
from FileUtilities.Settings import load_settings

log = logging.getLogger(__name__)

#TODO: Improve logging for async. Add write out to file handler, which outputs txt for each file, and configure logging in each thread.
logging.basicConfig(level=logging.INFO)

#Load Game
def convert_game_images(game_path):
    """Converts all images for a given game path, including mods"""
    gameloader = RSEGameLoader()
    gameloaded = gameloader.load_game(game_path)
    if gameloaded is False:
        log.error("Failed to load game path")
        return
    #TODO: enumerate mods and then convert textures

    dataPath = path.join(game_path, "data")

    cxpDefinitions = load_relevant_cxps(dataPath)

    imagePaths = gather_files_in_path(".RSB", dataPath)

    for filepath in imagePaths:
        log.info("Processing: %s", filepath)
        imageFile = RSBImageFile()
        imageFile.read_file(filepath)
        filename = path.basename(filepath)

        original_texture_name = restore_original_texture_name(filename)
        cxpDef = get_cxp_definition(cxpDefinitions, original_texture_name)

        colorKeyRGB = None
        if cxpDef is not None:
            log.info("Matched CXP definition: %s", original_texture_name)
            if cxpDef.blendMode == "colorkey":
                colorKeyRGB = cxpDef.colorkey

        image = None

        if colorKeyRGB is not None:
            colorkeyMask = tuple(colorKeyRGB)
            image = imageFile.convert_full_color_image_with_colorkey_mask(colorkeyMask)
        else:
            image = imageFile.convert_full_color_image()
        PNGFilename = filepath + settings["imageCacheSuffix"]
        image.save(PNGFilename, settings["imageCacheFormat"])

if __name__ == "__main__":
    settings = load_settings()
    gamepath = settings["gamePath"]
    convert_game_images(gamepath)
