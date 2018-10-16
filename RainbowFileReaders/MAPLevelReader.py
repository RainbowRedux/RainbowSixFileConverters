from RainbowFileReaders import BinaryConversionUtilities
from RainbowFileReaders import R6Settings
from RainbowFileReaders.SOBModelReader import RSEMaterialListHeader, RSEMaterialDefinition
from datetime import datetime

class MAPLevelFile(object):
    """Class to read full SOB files"""
    def __init__(self):
        super(MAPLevelFile, self).__init__()
        self.header = None
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []
        self.footer = None

    def read_map(self, filename, verboseOutput=False):
        mapFile = BinaryConversionUtilities.BinaryFileReader(filename)

        self.header = MAPHeader()
        self.header.read_header(mapFile)
        if verboseOutput:
            self.header.print_header_info()

        self.materialListHeader = RSEMaterialListHeader()
        self.materialListHeader.read_header(mapFile)
        if verboseOutput:
            self.materialListHeader.print_header_info()

        self.materials = []
        for _ in range(self.materialListHeader.numMaterials):
            newMaterial = RSEMaterialDefinition()
            newMaterial.read_material(mapFile)
            self.materials.append(newMaterial)
            if verboseOutput:
                newMaterial.print_material_info()
        
        return

        self.geometryListHeader = SOBGeometryListHeader()
        self.geometryListHeader.read_header(mapFile)
        if verboseOutput:
            self.geometryListHeader.print_header_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            newObj = SOBGeometryObject()
            newObj.read_object(mapFile)
            self.geometryObjects.append(newObj)
            if verboseOutput:
                newObj.print_object_info()

        self.footer = SOBFooterDefinition()
        self.footer.read_footer(mapFile)
        
        print("Processed: " + str(mapFile.get_seekg()) + " bytes")
        print("Length: " + str(mapFile.get_length()) + " bytes")
        print("Unprocessed: " + str(mapFile.get_length() - mapFile.get_seekg()) + " bytes")


class MAPHeader(object):
    def __init__(self):
        super(MAPHeader, self).__init__()
        self.headerLength = 0
        self.headerBeginMessage = None
        self.time = datetime.now()
        self.timePOSIXRaw = 0

    def read_header(self, filereader):
        self.headerLength = filereader.read_uint()
        self.headerBeginMessageRaw = filereader.read_bytes(self.headerLength)
        self.headerBeginMessage = self.headerBeginMessageRaw[:-1].decode("utf-8")
        self.timePOSIXRaw = filereader.read_uint()
        #special case handling, some files have a zero timestamp recorded, which datetime.fromtimestamp() doesn't like
        if self.timePOSIXRaw == 0:
            self.time = datetime(1970,1,1)
        else:
            self.time = datetime.fromtimestamp(self.timePOSIXRaw)

    def print_header_info(self):
        print("Header length: " + str(self.headerLength))
        print("Header message: " + str(self.headerBeginMessage))
        print("Saved time: " + str(self.time.strftime('%d/%m/%Y %H:%M:%S')))
        print("")

class MAPMaterialDefinition(object):
    def __init__(self):
        super(MAPMaterialDefinition, self).__init__()
        self.materialSize = None
        self.ID = None
        self.materialNameLength = None
        self.materialName = None
        self.materialNameRaw = None
        self.textureNameLength = None
        self.textureName = None
        self.textureNameRaw = None
        self.opacity = None
        self.unknown2 = None
        self.alphaMethod = None
        self.ambient = None
        self.diffuse = None
        self.specular = None
        self.specularLevel = None
        self.twoSided = None

    def read_material(self, filereader):
        self.materialSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.versionStringLength = filereader.read_uint()
        self.versionNumber = None
        if self.versionStringLength == 8:
            self.versionStringRaw = filereader.read_bytes(self.versionStringLength)
            if self.versionStringRaw[:-1] == b'Version':
                self.versionNumber = filereader.read_uint()
                self.materialNameLength = filereader.read_uint()
                self.materialNameRaw = filereader.read_bytes(self.materialNameLength)
            else:
                self.materialNameLength = self.versionStringLength
                self.materialNameRaw = self.versionStringRaw
        else:
            self.materialNameLength = self.versionStringLength
            self.materialNameRaw = filereader.read_bytes(self.materialNameLength)

        self.textureNameLength = filereader.read_uint()
        self.textureNameRaw = filereader.read_bytes(self.textureNameLength)

        self.opacity = filereader.read_float()
        self.unknown2 = filereader.read_float() # Full lit?
        self.alphaMethod = filereader.read_uint() # Smoothing according to AK? Transparency method? Best guess at the moment is transparency method. 1 = SOLID, 2 = MASKED, 3 = ALPHA_BLEND
        self.ambient = filereader.read_rgb_color_24bpp_uint()
        self.diffuse = filereader.read_rgb_color_24bpp_uint()
        self.specular = filereader.read_rgb_color_24bpp_uint()
        self.specularLevel = filereader.read_float()
        self.twoSided = filereader.read_bytes(1)

        self.textureName = self.textureNameRaw[:-1].decode("utf-8")
        self.materialName = self.materialNameRaw[:-1].decode("utf-8")


    def print_material_info(self):
        print("Material size: " + str(self.materialSize))
        print("ID: " + str(self.ID))
        print("Material Name Length: " + str(self.materialNameLength))
        print("Material Name: " + str(self.materialName.decode("utf-8")))
        print("Texture Name Length: " + str(self.textureNameLength))
        print("Texture Name: " + str(self.textureName.decode("utf-8")))
        print("")