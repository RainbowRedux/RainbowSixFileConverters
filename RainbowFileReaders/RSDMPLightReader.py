from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader

class RSDMPLightFile(FileFormatReader):
    """Class to read full RSB files"""
    def __init__(self):
        super(RSDMPLightFile, self).__init__()
    
    def read_data(self):
        super().read_data()

        filereader = self._filereader

        self.header = RSDMPHeader()
        self.header.read(filereader)
        
        self.lights = []
        for _ in range(self.header.lightCount):
            newLight = RSDMPLight()
            newLight.read(filereader)
            self.lights.append(newLight)

class RSDMPHeader(BinaryFileDataStructure):
    """Reads and stores the header of DMP files from Rogue Spear"""
    def __init__(self):
        super(RSDMPHeader, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.FileID = filereader.read_uint()
        self.AmbientLightColor = filereader.read_vec_f(4)
        self.unknown5 = filereader.read_uint()
        self.lightCount = filereader.read_uint()

class RSDMPLight(BinaryFileDataStructure):
    """Reads and stores Light structures from Rogue spear DMP files."""
    def __init__(self):
        super(RSDMPLight, self).__init__()

    def read(self, filereader):
        super().read(filereader)

        self.read_named_string(filereader, "parentRoomString")

        self.read_name_string(filereader)
        if self.nameString == "Version":
            self.versionString = self.nameString
            self.versionStringRaw = self.nameStringRaw
            self.versionStringLength = self.nameStringLength
            self.versionNumber = filereader.read_uint()

            self.read_name_string(filereader)
            self.unknown6 = filereader.read_bytes(1)[0]

        self.lightType = filereader.read_uint()
        self.direction = filereader.read_vec_f(3)
        self.position = filereader.read_vec_f(3)
        self.falloff = filereader.read_float()
        self.unknown2 = filereader.read_vec_f(2)
        self.unknown3 = filereader.read_vec_f(3)

        self.energy = filereader.read_float()
        self.diffuseColor = filereader.read_vec_f(4)
        self.specularColor = filereader.read_vec_f(4)
        self.ambientColor = filereader.read_vec_f(4)
        self.constantAttenuation = filereader.read_float()
        self.linearAttenuation = filereader.read_float()
        self.quadraticAttenuation = filereader.read_float()
        self.spotlightConeAngle = filereader.read_float()
        self.type = filereader.read_bytes(1)[0]