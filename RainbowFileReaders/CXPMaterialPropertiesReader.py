"""
Classes and functions to load and parse CXP material property files
"""
import os
import logging

from typing import List, Dict, Optional

from RainbowFileReaders import R6Settings
from FileUtilities.TextFileUtilities import read_tokenized_text_file

log = logging.getLogger(__name__)

class CXPMaterialProperties(object):
    """Material properties associated with a single texture/material"""
    def __init__(self):
        super(CXPMaterialProperties, self).__init__()
        self.type: str = ""
        #Actually just texture name
        self.materialName: str = None
        #Should be alpha-transparent in software rendering mode
        self.softwarealpha: bool = False
        #Default to opaque mode,
        self.blendMode: str = "opaque"
        #If this is not empty, this is the color that should act as the alpha mask. It's often slightly off by 1 due to imprecision in 16bit color images, so take that into accound when using this value
        self.colorkey: List[int] = []
        #This appears to describe maximum Min/Mag texture filtering modes. Final value for a given texture seems to be min(UserOption, TextureOption)
        self.mipMapValues: List[str] = []
        #Determines if gunfire/bullets can pass through this material
        self.gunpass: bool = False
        #Determines if grenades can pass through this material
        self.grenadepass: bool = False
        #Parameters around the texture format. Not sure what the leading 0 is, but the rest appear to be RGBA bit depths, eg. 4, 4, 4, 4 for a 16bit texture with an alpha channel
        #This mainly appears to be a property used when generating RSB files.
        self.textureformat: List[int] = []
        #additional textures that should be added to the image sequence
        self.animated: bool = False
        self.animTypeRaw: str = ""
        self.animInterval: float = 0.0
        self.animNumAdditionalTextures: int = 0
        self.animAdditionalTextures: List[str] = []
        #disables mipmapping?
        self.nosubsamble: bool = False
        #Scroll rates, empty if not enabled
        self.scrolling: bool = False
        self.scrollParams: List[float] = []

    def read_properties(self, keywords: List[str]):
        """Reads a single textures' set of material properties"""
        bFoundEnd = False
        while bFoundEnd is False:
            currKeyword = keywords.pop(0)
            if currKeyword.lower() == "end":
                bFoundEnd = True
                break

            if currKeyword == "mipmap":
                #read 2 values for this
                #TODO: Work out what these values mean
                self.mipMapValues.append(keywords.pop(0))
                self.mipMapValues.append(keywords.pop(0))
            elif currKeyword == "colorkey":
                #Set the blend mode, and grab the RGB color key
                self.blendMode = currKeyword
                #to handle cases of multiple definitions clear the color key
                self.colorkey = []
                for _ in range(3):
                    self.colorkey.append(int(keywords.pop(0)))
            elif currKeyword == "textureformat":
                #read the 5 values specified with a texture format
                #TODO: Work out what most of these values mean. Confirm final 4 values are RGBA bitdepth
                for _ in range(5):
                    self.textureformat.append(int(keywords.pop(0)))
            elif currKeyword == "alphablend":
                self.blendMode = currKeyword
            elif currKeyword == "gunpass":
                self.gunpass = True
            elif currKeyword == "grenadepass":
                self.grenadepass = True
            elif currKeyword == "softwarealpha":
                self.softwarealpha = True
            elif currKeyword == "nosubsample":
                self.nosubsamble = True
            elif currKeyword == "animated":
                self.animated = True
                self.animTypeRaw = keywords.pop(0)
                self.animInterval = float(keywords.pop(0))
                self.animNumAdditionalTextures = int(keywords.pop(0))
                for _ in range(self.animNumAdditionalTextures):
                    self.animAdditionalTextures.append(keywords.pop(0))
            elif currKeyword in ("scroll", "scrolling"):
                self.scrolling = True
                for _ in range(3):
                    self.scrollParams.append(float(keywords.pop(0)))
            else:
                log.warning("Skipping: %s", currKeyword)

def read_cxp(path: str) -> List[CXPMaterialProperties]:
    """Loads and parses a CXP and returns a list of material properties"""
    keywords = read_tokenized_text_file(path)
    MaterialPropertiesDict: Dict[str, CXPMaterialProperties] = {}
    while keywords:
        try:
            if keywords[0].strip() != "Material" and keywords[0] != "Surface":
                raise ValueError("Not a valid material begin statement: " + keywords[0])

            newType = keywords.pop(0)
            newMaterialName = keywords.pop(0)
            # The CXP key is the lowercase texture name, since this was a windows game, filename case is irrelevant
            materialKey = newMaterialName.lower()
            newMat = None
            if materialKey in MaterialPropertiesDict:
                newMat = MaterialPropertiesDict[materialKey]
            else:
                newMat = CXPMaterialProperties()
                newMat.type = newType
                newMat.materialName = newMaterialName
                MaterialPropertiesDict[materialKey] = newMat

            newMat.read_properties(keywords)
        except ValueError as ve:
            #In this instance, there is an invalid CXP material
            #One such instance is the Rommel.CXP file in the classic missions included with Urban Operations includes an extra "End" statement at the bottom, which is invalid
            #remove this errored keyword so that program can continue
            discardedWord = keywords.pop(0)
            log.error("Skipping invalid material definition in CXP: %s", str(ve))
            log.error("\tDiscarded keyword: %s", discardedWord)

    # Create and return a list of CXP properties, as many CXP files will be combined, and the order is important for matching
    MaterialProperties: List[CXPMaterialProperties] = []
    for _, val in MaterialPropertiesDict.items():
        MaterialProperties.append(val)
    return MaterialProperties

def load_relevant_cxps(datapath: str, modpath: Optional[str] = None) -> List[CXPMaterialProperties]:
    """Given the main datapath for a game installation, and optionally a modpath,
    this will load the appropriate CXPs and then merge the results into a single list"""
    dataTexturePath: str = ""
    if datapath is not None:
        dataTexturePath = os.path.join(datapath, R6Settings.paths["TexturePath"])

    modTexturePath: str = ""
    if modpath is not None:
        modTexturePath = os.path.join(modpath, R6Settings.paths["TexturePath"])

    CXPFilesToRead = []

    #Add the mod texture path first, so entries from here take priority
    if modTexturePath:
        modShermanPath = os.path.join(modTexturePath, "Sherman.CXP")
        modRommelPath = os.path.join(modTexturePath, "Rommel.CXP")
        if os.path.isfile(modShermanPath):
            CXPFilesToRead.append(modShermanPath)
        if os.path.isfile(modRommelPath):
            CXPFilesToRead.append(modRommelPath)

    if dataTexturePath:
        dataShermanPath = os.path.join(dataTexturePath, "Sherman.CXP")
        dataRommelPath = os.path.join(dataTexturePath, "Rommel.CXP")
        if os.path.isfile(dataShermanPath):
            CXPFilesToRead.append(dataShermanPath)
        if os.path.isfile(dataRommelPath):
            CXPFilesToRead.append(dataRommelPath)

    CXPDefinitions: List[CXPMaterialProperties] = []
    for cxpPath in CXPFilesToRead:
        tempCXPDefs = read_cxp(cxpPath)
        CXPDefinitions.extend(tempCXPDefs)

    return CXPDefinitions

def get_cxp_definition(CXPDefinitions: List[CXPMaterialProperties], texture_name: str) -> Optional[CXPMaterialProperties]:
    """
    Iterates through a list of CXPs to find a definition that matches the texture
    texture_name should be the source texture name, not the RSB texture name.
    Comparison is case insensitive.
    """
    for cxp in CXPDefinitions:
        #Match on lowercase since it's a windows game and windows has no concept of case sensitive filenames
        if cxp.materialName.lower() == texture_name.lower():
            log.debug("Matched CXP: %s", cxp.materialName)
            return cxp

    return None
