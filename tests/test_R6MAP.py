"""Test reading MAP files from Rainbow Six (1998)"""

import unittest
from os import path

from Settings import load_settings
from RainbowFileReaders import MAPLevelReader

class R6MAPTests(unittest.TestCase):
    """Test R6 MAPs"""

    def test_R6_MAP_Structure(self):
        """Tests reading an R6 MAP file"""
        settings = load_settings("test_settings.json")

        RSB_filepath = path.join(settings["gamePath_R6_EW"], "data", "map", "m01", "M01.map")

        loadedFile = MAPLevelReader.MAPLevelFile()
        readSucessfullyToEOF = loadedFile.read_file(RSB_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        self.assertEqual(loadedFile.materialListHeader.numMaterials, 263, "Unexpected number of materials")

        self.assertEqual(loadedFile.geometryListHeader.count, 57, "Unexpected number of geometry objects")

        self.assertEqual(loadedFile.portalList.portalCount, 65, "Unexpected number of portals")

        self.assertEqual(loadedFile.lightList.lightCount, 162, "Unexpected number of lights")

        self.assertEqual(loadedFile.objectList.objectCount, 38, "Unexpected number of objects")

        self.assertEqual(loadedFile.roomList.roomCount, 47, "Unexpected number of rooms")

        self.assertEqual(loadedFile.planningLevelList.planningLevelCount, 4, "Unexpected number of planning levels")

        self.assertEqual(loadedFile.mapFooter.EndMapString, "EndMap", "Unexpected end of map footer string")

if __name__ == '__main__':
    unittest.main()