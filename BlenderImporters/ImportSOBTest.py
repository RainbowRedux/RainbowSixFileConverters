import sys
import importlib

# TODO: find a better way to load this module from Blender.
sys.path.insert(0, 'C:/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')

from BlenderImporters import ImportSOB
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders import BinaryConversionUtilities

importlib.reload(BinaryConversionUtilities)
importlib.reload(ImportSOB)
importlib.reload(SOBModelReader)
importlib.reload(R6Settings)

ImportSOB.import_SOB_to_scene("C:\\Users\\philipedwards\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\model\\cessna.sob")
ImportSOB.import_SOB_to_scene("C:\\Users\\philipedwards\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\model\\computer.sob")
ImportSOB.import_SOB_to_scene("C:\\Users\\philipedwards\\Dropbox\\Development\\Rainbow\\Data\\R6GOG\\data\\model\\mp5.sob")

