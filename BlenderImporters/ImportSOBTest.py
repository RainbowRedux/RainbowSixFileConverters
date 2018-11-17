import sys
import importlib

# TODO: find a better way to load this module from Blender.
sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')

from BlenderImporters import ImportSOB
from RainbowFileReaders import MathHelpers
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders import BinaryConversionUtilities

importlib.reload(MathHelpers)
importlib.reload(R6Settings)
importlib.reload(BinaryConversionUtilities)
importlib.reload(SOBModelReader)
importlib.reload(ImportSOB)

ImportSOB.import_SOB_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\model\\cessna.sob")
ImportSOB.import_SOB_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\model\\computer.sob")
ImportSOB.import_SOB_to_scene("E:\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\model\\mp5.sob")