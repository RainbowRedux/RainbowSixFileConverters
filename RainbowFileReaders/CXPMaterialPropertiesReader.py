import shlex
import os

from RainbowFileReaders import R6Settings

class CXPMaterialProperties(object):
    def __init__(self):
        super(CXPMaterialProperties, self).__init__()
        self.materialName = None
        self.softwarealpha = False
        self.blendMode = "opaque"
        self.colorkey = []
        self.mipMapValues = []
        self.gunpass = False
        self.grenadepass = False
        self.textureformat = []
        self.animAdditionalTextures = []
        self.nosubsamble = False
        self.scrollParams = []

    def read(self, keywords):
        if keywords[0].strip() != "Material" and keywords[0] != "Surface":
            raise ValueError("Not a valid material begin statement: " + keywords[0] + keywords[1])

        self.type = keywords.pop(0)
        self.materialName = keywords.pop(0)
        bFoundEnd = False
        while bFoundEnd is False:
            currKeyword = keywords.pop(0)
            if currKeyword.lower() == "end":
                bFoundEnd = True
                break
            elif currKeyword == "mipmap":
                #read 2 values for this
                #TODO: Work out what these values mean
                self.mipMapValues.append(keywords.pop(0))
                self.mipMapValues.append(keywords.pop(0))
            elif currKeyword == "colorkey":
                #Set the blend mode, and grab the RGB color key
                self.blendMode = currKeyword
                self.colorkey.append(keywords.pop(0))
                self.colorkey.append(keywords.pop(0))
                self.colorkey.append(keywords.pop(0))
            elif currKeyword == "textureformat":
                #read the 5 values specified with a texture format
                #TODO: Work out what most of these values mean. Confirm final 4 values are RGBA bitdepth
                self.textureformat.append(keywords.pop(0))
                self.textureformat.append(keywords.pop(0))
                self.textureformat.append(keywords.pop(0))
                self.textureformat.append(keywords.pop(0))
                self.textureformat.append(keywords.pop(0))
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
                self.animtypeRaw = keywords.pop(0)
                self.animInterval = keywords.pop(0)
                self.animNumAdditionalTextures = int(keywords.pop(0))
                for _ in range(self.animNumAdditionalTextures):
                    self.animAdditionalTextures.append(keywords.pop(0))
            elif currKeyword == "scroll" or currKeyword == "scrolling":
                self.scrollParams.append(keywords.pop(0))
                self.scrollParams.append(keywords.pop(0))
                self.scrollParams.append(keywords.pop(0))
            else:
                print("Skipping: " + currKeyword)

def _read_cxp_keywords(path):
    """Reads a text file and tokenizes.
    Keeps strings within quotes, and discards comments"""
    inFile = open(path, "r")
    lines = inFile.readlines()
    cxp_keywords = []
    for line in lines:
        line_values = shlex.split(line)
        for value in line_values:
            if value.startswith("//"):
                #this is a comment, so the rest of this line can be skipped
                break
            else:
                cxp_keywords.append(value)
    return cxp_keywords

def read_cxp(path):
    keywords = _read_cxp_keywords(path)
    MaterialProperties = []
    while len(keywords) > 0:
        newMat = CXPMaterialProperties()
        try:
            newMat.read(keywords)
        except:
            #In this instance, there is an invalid CXP material
            #One such instance is the Rommel.CXP file in the classic missions included with Urban Operations includes an extra "End" statement at the bottom, which is invalid
            #remove this errored keyword so that program can continue
            discardedWord = keywords.pop(0)
            print("Skipping invalid material definition in CXP")
            print("\tDiscarded keyword: " + discardedWord)
        MaterialProperties.append(newMat)
    return MaterialProperties

def load_relevant_cxps(datapath, modpath = None):
    dataTexturePath = None
    if datapath is not None:
        dataTexturePath = os.path.join(datapath, R6Settings.paths["TexturePath"])

    modTexturePath = None
    if modpath is not None:
        modTexturePath = os.path.join(modpath, R6Settings.paths["TexturePath"])
    
    CXPFilesToRead = []

    #Add the mod texture path first, so entries from here take priority
    if modTexturePath is not None:
        modShermanPath = os.path.join(modTexturePath, "Sherman.CXP")
        modRommelPath = os.path.join(modTexturePath, "Rommel.CXP")
        if os.path.isfile(modShermanPath):
            CXPFilesToRead.append(modShermanPath)
        if os.path.isfile(modRommelPath):
            CXPFilesToRead.append(modRommelPath)

    if dataTexturePath is not None:
        dataShermanPath = os.path.join(dataTexturePath, "Sherman.CXP")
        dataRommelPath = os.path.join(dataTexturePath, "Rommel.CXP")
        if os.path.isfile(dataShermanPath):
            CXPFilesToRead.append(dataShermanPath)
        if os.path.isfile(dataRommelPath):
            CXPFilesToRead.append(dataRommelPath)
    
    CXPDefinitions = []
    for cxpPath in CXPFilesToRead:
        tempCXPDefs = read_cxp(cxpPath)
        CXPDefinitions.extend(tempCXPDefs)

    return CXPDefinitions

def test():
    #read_cxp("/Users/philipedwards/Dropbox/Development/Rainbow/Data/R6GOG/data/texture/Sherman.CXP")
    read_cxp("E:\\Dropbox\\Development\\Rainbow\\Data\\Test\\CXPs\\Rommel.CXP")
    read_cxp("E:\\Dropbox\\Development\\Rainbow\\Data\\Test\\CXPs\\Sherman.CXP")

if __name__ == "__main__":
    test()