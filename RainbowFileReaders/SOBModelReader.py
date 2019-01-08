from FileUtilities import BinaryConversionUtilities
from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import RSEMaterialFormatConstants, RSEGameVersions
from RainbowFileReaders.RSEMaterialDefinition import RSEMaterialDefinition, RSEMaterialListHeader
from RainbowFileReaders.CXPMaterialPropertiesReader import load_relevant_cxps
from RainbowFileReaders.RSEGeometryDataStructures import R6GeometryObject, RSEGeometryListHeader

class SOBModelFile(FileFormatReader):
    """Class to read full SOB files"""
    def __init__(self):
        super(SOBModelFile, self).__init__()
        self.header = None
        self.materialListHeader = None
        self.materials = []
        self.geometryListHeader = None
        self.geometryObjects = []
        self.footer = None

    def read_data(self):
        super().read_data()

        fileReader = self._filereader

        self.header = SOBHeader()
        self.header.read(fileReader)
        if self.verboseOutput:
            self.header.print_structure_info()

        self.materialListHeader = RSEMaterialListHeader()
        self.materialListHeader.read(fileReader)
        if self.verboseOutput:
            self.materialListHeader.print_structure_info()

        _, gameDataPath, modPath = R6Settings.determine_data_paths_for_file(self.filepath)
        CXPDefinitions = load_relevant_cxps(gameDataPath, modPath)

        self.materials = []
        for _ in range(self.materialListHeader.numMaterials):
            newMaterial = RSEMaterialDefinition()
            newMaterial.read(fileReader)
            newMaterial.add_CXP_information(CXPDefinitions)
            self.materials.append(newMaterial)
            if self.verboseOutput:
                newMaterial.print_structure_info()

        self.geometryListHeader = RSEGeometryListHeader()
        self.geometryListHeader.read(fileReader)
        if self.verboseOutput:
            self.geometryListHeader.print_structure_info()

        self.geometryObjects = []
        for _ in range(self.geometryListHeader.count):
            newObj = R6GeometryObject()
            newObj.read(fileReader)
            self.geometryObjects.append(newObj)
            if self.verboseOutput:
                pass
                #newObj.print_structure_info()

        self.footer = SOBFooterDefinition()
        self.footer.read(fileReader)


class SOBHeader(BinaryFileDataStructure):
    def __init__(self):
        super(SOBHeader, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_named_string(filereader, "headerBeginMessage")


class SOBFooterDefinition(BinaryFileDataStructure):
    def __init__(self):
        super(SOBFooterDefinition, self).__init__()

    def read(self, filereader):
        super().read(filereader)
        self.read_named_string(filereader, "EndModelString")

if __name__ == "__main__":
    test = SOBModelFile()
