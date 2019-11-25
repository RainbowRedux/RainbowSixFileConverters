"""
Loads a game path and then converts all RSBs within to full colour PNGs with the extension .CACHE.PNG
"""

from os import path

from RainbowFileReaders.CXPMaterialPropertiesReader import load_relevant_cxps, get_cxp_definition
from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.RSBImageReader import RSBImageFile
from RainbowFileReaders.R6Settings import restore_original_texture_name
from FileUtilities.DirectoryUtils import gather_files_in_path

#Load Game
def convert_game_images(game_path):
    """Converts all images for a given game path, including mods"""
    gameloader = RSEGameLoader()
    gameloaded = gameloader.load_game(game_path)
    if gameloaded is False:
        print("Failed to load game path")
        return
    #TODO: enumerate mods and then convert textures

    dataPath = path.join(game_path, "data")

    cxpDefinitions = load_relevant_cxps(dataPath)

    imagePaths = gather_files_in_path(".RSB", dataPath)

    for filepath in imagePaths:
        print("Processing: " + filepath)
        imageFile = RSBImageFile()
        imageFile.read_file(filepath)
        filename = path.basename(filepath)

        original_texture_name = restore_original_texture_name(filename)
        cxpDef = get_cxp_definition(cxpDefinitions, original_texture_name)

        colorKeyRGB = None
        if cxpDef is not None:
            print("Matched CXP definition: " + original_texture_name)
            if cxpDef.blendMode == "colorkey":
                colorKeyRGB = cxpDef.colorkey

        image = None

        if colorKeyRGB is not None:
            colokeyMask = tuple(colorKeyRGB)
            image = imageFile.convert_full_color_image_with_colorkey_mask(colokeyMask)
        else:
            image = imageFile.convert_full_color_image()
        PNGFilename = filepath + ".CACHE.PNG"
        image.save(PNGFilename, "PNG")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate cached PNGs for each RSB in a game')
    parser.add_argument('gamepath', help='the path to the game to process')

    args = parser.parse_args()
    print("Gamepath: " + args.gamepath)
    convert_game_images(args.gamepath)
