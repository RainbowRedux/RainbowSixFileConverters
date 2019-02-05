"""A script for unattended Map file importing and export to FBX"""
import sys

# TODO: find a better way to load this module from Blender.
sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')

from FileUtilities import DirectoryProcessor
from BlenderImporters import ImportMAP

def ExportAllMaps():
    """Processes all maps in path and then exports to FBX"""
    paths = []
    #paths.append("TestData/ReducedGames/R6GOG")
    paths.append("TestData/ReducedGames/")
    #paths.append("FullGames")
    import ProcessorPathsHelper
    paths = ProcessorPathsHelper.expand_paths(paths)

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths = fp.paths + paths
    fp.fileExt = ".MAP"

    fp.processFunction = ImportMAP.import_map_and_save

    fp.run_sequential()

if __name__ == "__main__":
    ExportAllMaps()
