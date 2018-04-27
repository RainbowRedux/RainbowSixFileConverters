import BinaryConversionUtilities


class SOBModelFile(object):
    """Class to read full SOB files"""
    def __init__(self):
        pass

    def read_sob(self, filename):
        modelFile = BinaryConversionUtilities.BinaryFileReader(filename)

        self.header = SOBHeader()
        self.header.read_header(modelFile)
        self.header.print_header_info()

        self.material_list_header = SOBMaterialListHeader()
        self.material_list_header.read_header(modelFile)
        self.material_list_header.print_header_info()

        self.materials = []
        for i in range(self.material_list_header.numMaterials):
            newMaterial = SOBMaterialDefinition()
            newMaterial.read_material(modelFile)
            newMaterial.print_material_info()

            self.materials.append(newMaterial)

        
        print("Processed: " + str(modelFile.get_seekg()) + " bytes")
        print("Length: " + str(modelFile.get_length()) + " bytes")
        print("Unprocessed: " + str(modelFile.get_length() - modelFile.get_seekg()) + " bytes")


class SOBHeader(object):
    def __init__(self):
        self.headerLength = 0
        self.headerBeginMessage = None

    def read_header(self, filereader):
        self.headerLength = filereader.read_uint()
        self.headerBeginMessage = filereader.read_bytes(self.headerLength)

    def print_header_info(self):
        print("Header length: " + str(self.headerLength))
        print("Header message: " + str(self.headerBeginMessage))
        print("")

class SOBMaterialListHeader(object):
    def __init__(self):
        pass

    def read_header(self, filereader):
        self.materialListSize = filereader.read_uint()
        self.unknown1 = filereader.read_uint()
        self.materialBeginMessageLength = filereader.read_uint()
        self.materialBeginMessage = filereader.read_bytes(self.materialBeginMessageLength)
        self.numMaterials = filereader.read_uint()

    def print_header_info(self):
        print("Material list size: " + str(self.materialListSize))
        print("unknown1: " + str(self.unknown1))
        print("Number of materials: " + str(self.numMaterials))
        print("Begin message length: " + str(self.materialBeginMessageLength))
        print("Begin message: " + str(self.materialBeginMessage))
        print("")


class SOBMaterialDefinition(object):
    def __init__(self):
        pass

    def read_material(self, filereader):
        self.materialSize = filereader.read_uint()
        self.ID = filereader.read_uint()

        self.versionStringLength = filereader.read_uint()
        self.versionNumber = None
        if self.versionStringLength == 8:
            self.versionString = filereader.read_bytes(self.versionStringLength)
            if self.versionString[:-1] == b'Version':
                self.versionNumber = filereader.read_uint()
                self.materialNameLength = filereader.read_uint()
        if self.versionNumber is None:
            self.materialNameLength = self.versionStringLength
        self.materialName = filereader.read_bytes(self.materialNameLength)

        self.textureNameLength = filereader.read_uint()
        self.textureName = filereader.read_bytes(self.textureNameLength)

        self.opacity = filereader.read_float()
        self.unknown2 = filereader.read_float()
        self.unknown3 = filereader.read_uint()
        self.ambient = filereader.read_rgb_color_32bpp_uint()
        self.diffuse = filereader.read_rgb_color_32bpp_uint()
        self.specular = filereader.read_rgb_color_32bpp_uint()
        self.specularLevel = filereader.read_float()
        self.twoSided = filereader.read_bytes(1)


    def print_material_info(self):
        print("Material size: " + str(self.materialSize))
        print("ID: " + str(self.ID))
        print("Material Name Length: " + str(self.materialNameLength))
        print("Material Name " + str(self.materialName))
        print("Texture Name Length: " + str(self.textureNameLength))
        print("Texture Name: " + str(self.textureName))
        print("")