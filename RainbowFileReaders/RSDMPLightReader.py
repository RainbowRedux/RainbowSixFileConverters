""" This module contains classes to read DMP files that are associated with Rainbow Six Rogue Spear maps. These are light definitions """

from typing import List

from FileUtilities.BinaryConversionUtilities import BinaryFileDataStructure, FileFormatReader, SizedCString, BinaryFileReader


class RSDMPLightFile(FileFormatReader):
    """Class to read full RSB files"""
    def __init__(self):
        super(RSDMPLightFile, self).__init__()
        self.header: RSDMPHeader = RSDMPHeader()
        self.lights: List[RSDMPLight] = []

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

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.FileID: int = filereader.read_uint32()
        self.AmbientLightColor: List[float] = filereader.read_vec_f(4)
        self.unknown5: int = filereader.read_uint32()
        self.lightCount: int = filereader.read_uint32()

class RSDMPLight(BinaryFileDataStructure):
    """Reads and stores Light structures from Rogue spear DMP files."""
    def __init__(self):
        super(RSDMPLight, self).__init__()

    def read(self, filereader: BinaryFileReader):
        super().read(filereader)

        self.parent_room_string: SizedCString = SizedCString(filereader)

        self.name_string: SizedCString = SizedCString(filereader)
        if self.name_string.string == "Version":
            self.version_string: SizedCString = self.name_string
            self.versionNumber: int = filereader.read_uint32()
            self.name_string = SizedCString(filereader)

            self.unknown6: int = filereader.read_bytes(1)[0]

        self.lightType: int = filereader.read_uint32()
        self.direction: List[float] = filereader.read_vec_f(3)
        self.position: List[float] = filereader.read_vec_f(3)
        self.falloff: float = filereader.read_float()
        self.unknown2: List[float] = filereader.read_vec_f(2)
        self.unknown3: List[float] = filereader.read_vec_f(3)

        self.energy: float = filereader.read_float()
        self.diffuseColor: List[float] = filereader.read_vec_f(4)
        self.specularColor: List[float] = filereader.read_vec_f(4)
        self.ambientColor: List[float] = filereader.read_vec_f(4)
        self.constantAttenuation: float = filereader.read_float()
        self.linearAttenuation: float = filereader.read_float()
        self.quadraticAttenuation: float = filereader.read_float()
        self.spotlightConeAngle: float = filereader.read_float()
        self.type: int = filereader.read_bytes(1)[0]
