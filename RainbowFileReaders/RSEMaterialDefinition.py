"""Provides classes that will read and parse Material definitions and related information in RSE game formats."""
import logging

from typing import List

from RainbowFileReaders.R6Constants import RSEGameVersions, RSEMaterialFormatConstants
from RainbowFileReaders.MathHelpers import normalize_color, unnormalize_color
from RainbowFileReaders.CXPMaterialPropertiesReader import get_cxp_definition, CXPMaterialProperties
from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, SizedCString, BinaryFileReader

log = logging.getLogger(__name__)

class RSEMaterialListHeader(BinaryFileDataStructure):
    """Reads and stores information in the header of a material list"""
    def __init__(self):
        super().__init__()
        self.size: int = None
        self.unknown1: int = None
        self.material_list_string: SizedCString = SizedCString()
        self.numMaterials: int = None

    def read(self, filereader):
        super().read(filereader)

        self.size = filereader.read_uint32()
        self.unknown1 = filereader.read_uint32()
        self.material_list_string = SizedCString(filereader)
        self.numMaterials = filereader.read_uint32()


class RSEMaterialDefinition(BinaryFileDataStructure):
    """Reads, stores and provides functionality to use material information stored in RSE game formats"""
    def __init__(self):
        super(RSEMaterialDefinition, self).__init__()
        self.size: int = None
        self.id: int = None
        self.versionNumber: int = None
        self.opacity: float = None
        self.emissiveStrength: float = None
        self.textureAddressMode: int = None

        self.ambientColorUInt: List[int] = None
        self.ambientColorFloat: List[float] = None
        self.diffuseColorUInt: List[int] = None
        self.diffuseColorFloat: List[float] = None
        self.specularColorUInt: List[int] = None
        self.specularColorFloat: List[float] = None

        self.specularLevel: float = None
        self.twoSidedRaw: int = None
        self.twoSided: bool = None
        self.normalizedColors: bool = None
        self.CXPMaterialProperties: CXPMaterialProperties = None

    def get_material_game_version(self) -> str:
        """Returns the game this type of material is used in"""
        sizeWithoutStrings = self.size
        sizeWithoutStrings -= self.material_name.string_length
        sizeWithoutStrings -= self.version_string.string_length
        sizeWithoutStrings -= self.texture_name.string_length

        #check if it's a rainbow six file, or rogue spear file
        #Pylint disabled R1705 because stylistically i prefer this way here so i can extend it easier
        if sizeWithoutStrings == RSEMaterialFormatConstants.RSE_MATERIAL_SIZE_NO_STRINGS_RAINBOW_SIX or self.versionNumber is None:  # pylint: disable=R1705
            # Rainbow Six files typically have material sizes this size, or contain no version number
            return RSEGameVersions.RAINBOW_SIX
        else:
            #It's probably a Rogue Spear file
            #Material sizes in rogue spear files seem to be very inconsistent, so there needs to be a better detection method for future versions of the file
            #Actually, material sizes in rogue spear appear consistently as 69 if you just remove the texturename string length
            sizeWithoutStrings = self.size
            sizeWithoutStrings -= self.texture_name.string_length
            if sizeWithoutStrings == RSEMaterialFormatConstants.RSE_MATERIAL_SIZE_NO_STRINGS_ROGUE_SPEAR:
                return RSEGameVersions.ROGUE_SPEAR

        return RSEGameVersions.UNKNOWN

    def add_CXP_information(self, CXPDefinitions):
        """Takes a list of CXPMaterialProperties, and adds matching information"""
        cxp = get_cxp_definition(CXPDefinitions, self.texture_name.string)
        self.CXPMaterialProperties = cxp

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.size = filereader.read_uint32()
        self.ID = filereader.read_uint32()

        self.version_string = SizedCString(filereader)
        if self.version_string.string == 'Version':
            self.versionNumber = filereader.read_uint32()
            self.material_name = SizedCString(filereader)
        else:
            self.material_name = self.version_string

        self.texture_name = SizedCString(filereader)

        self.opacity = filereader.read_float()
        self.emissiveStrength = filereader.read_float()
        self.textureAddressMode = filereader.read_uint32() #1 = WRAP, 3 = CLAMP. https://docs.microsoft.com/en-au/windows/desktop/direct3d9/d3dtextureaddress

        gameVer = self.get_material_game_version()

        #check if it's a rainbow six file, or rogue spear file
        if gameVer == RSEGameVersions.RAINBOW_SIX:
            # Rainbow Six files typically have material sizes this size, or contain no version number
            self.ambientColorUInt = filereader.read_rgb_color_24bpp_uint()
            self.ambientColorFloat = list(normalize_color(self.ambientColorUInt))

            self.diffuseColorUInt = filereader.read_rgb_color_24bpp_uint()
            self.diffuseColorFloat = list(normalize_color(self.diffuseColorUInt))

            self.specularColorUInt = filereader.read_rgb_color_24bpp_uint()
            self.specularColorFloat = list(normalize_color(self.specularColorUInt))

            self.normalizedColors = False
        elif gameVer == RSEGameVersions.ROGUE_SPEAR:
            #It's a Rogue Spear file
            self.ambientColorFloat = filereader.read_rgba_color_32bpp_float()
            self.ambientColorUInt = list(unnormalize_color(self.ambientColorFloat))

            self.diffuseColorFloat = filereader.read_rgba_color_32bpp_float()
            self.diffuseColorUInt = list(unnormalize_color(self.diffuseColorFloat))

            self.specularColorFloat = filereader.read_rgba_color_32bpp_float()
            self.specularColorUInt = list(unnormalize_color(self.specularColorFloat))

            self.normalizedColors = True
        else:
            log.warning("Unhandled case")

        self.specularLevel = filereader.read_float()
        self.twoSidedRaw = filereader.read_bytes(1)[0]
        #TODO: Find a better way to read floats, maybe make this a function
        self.twoSided = False
        if self.twoSidedRaw > 0:
            self.twoSided = True
