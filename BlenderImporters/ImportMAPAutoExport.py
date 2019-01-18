import sys

# TODO: find a better way to load this module from Blender.
sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')

from FileUtilities import DirectoryProcessor
from BlenderImporters import ImportMAP

def ExportAllMaps():
    paths = []
    paths.append("TestData/ReducedGames")
    import ProcessorPathsHelper
    paths = ProcessorPathsHelper.expand_paths(paths)

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths = fp.paths + paths
    fp.fileExt = ".MAP"

    fp.processFunction = ImportMAP.import_map_and_save

    fp.run_sequential()

if __name__ == "__main__":
    ExportAllMaps()
