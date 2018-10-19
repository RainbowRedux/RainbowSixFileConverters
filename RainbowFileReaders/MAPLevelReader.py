from RainbowFileReaders import BinaryConversionUtilities
from RainbowFileReaders import R6Settings
from RainbowFileReaders.SOBModelReader import RSEMaterialListHeader, RSEMaterialDefinition, RSEGeometryListHeader, SOBGeometryObject
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
                pass
                #newMaterial.print_material_info()

        self.geometryListHeader = RSEGeometryListHeader()
        self.geometryListHeader.read_header(mapFile)
        if verboseOutput:
            self.geometryListHeader.print_header_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            newObj = SOBGeometryObject()
            newObj.read_object(mapFile)
            self.geometryObjects.append(newObj)
            if verboseOutput:
                pass
                #newObj.print_object_info()
        
        return

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
