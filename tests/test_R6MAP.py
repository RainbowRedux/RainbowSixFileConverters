"""Test reading MAP files from Rainbow Six (1998)"""

import unittest
from os import path

from Settings import load_settings
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders.R6Constants import RSEGameVersions, RSEMaterialFormatConstants

TEST_SETTINGS_FILE = "test_settings.json"

class R6MAPTests(unittest.TestCase):
    """Test R6 MAPs"""

    def check_section_strings(self, loadedMapFile):
        """Check all strings in the mapFile are as expected"""
        self.assertEqual(loadedMapFile.header.headerBeginMessage, "BeginMapv2.1")
        self.assertEqual(loadedMapFile.materialListHeader.materialListBeginMessage, "MaterialList")
        self.assertEqual(loadedMapFile.geometryListHeader.geometryListString, "GeometryList")
        self.assertEqual(loadedMapFile.portalList.sectionString, "PortalList")
        self.assertEqual(loadedMapFile.lightList.sectionString, "LightList")
        self.assertEqual(loadedMapFile.objectList.sectionString, "ObjectList")
        self.assertEqual(loadedMapFile.roomList.sectionString, "RoomList")
        self.assertEqual(loadedMapFile.planningLevelList.sectionString, "PlanningLevelList")

        self.assertEqual(loadedMapFile.mapFooter.EndMapString, "EndMap", "Unexpected end of map footer string")


    def test_R6_MAP_Structure(self):
        """Tests reading an R6 MAP file, specifically M01"""
        settings = load_settings(TEST_SETTINGS_FILE)

        map_filepath = path.join(settings["gamePath_R6_EW"], "data", "map", "m01", "M01.map")

        loadedFile = MAPLevelReader.MAPLevelFile()
        readSucessfullyToEOF = loadedFile.read_file(map_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        self.check_section_strings(loadedFile)

        self.assertEqual(loadedFile.materialListHeader.numMaterials, 263, "Unexpected number of materials")

        self.assertEqual(loadedFile.geometryListHeader.count, 57, "Unexpected number of geometry objects")

        self.assertEqual(loadedFile.portalList.portalCount, 65, "Unexpected number of portals")

        self.assertEqual(loadedFile.lightList.lightCount, 162, "Unexpected number of lights")

        self.assertEqual(loadedFile.objectList.objectCount, 38, "Unexpected number of objects")

        self.assertEqual(loadedFile.roomList.roomCount, 47, "Unexpected number of rooms")

        self.assertEqual(loadedFile.planningLevelList.planningLevelCount, 4, "Unexpected number of planning levels")


    def test_R6_MAP_Materials(self):
        """Tests reading materials from an R6 MAP file"""
        settings = load_settings(TEST_SETTINGS_FILE)

        map_filepath = path.join(settings["gamePath_R6_EW"], "data", "map", "m02", "mansion.map")

        loadedFile = MAPLevelReader.MAPLevelFile()
        readSucessfullyToEOF = loadedFile.read_file(map_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")
        self.check_section_strings(loadedFile)

        self.assertEqual(loadedFile.materialListHeader.numMaterials, 137, "Unexpected number of materials")

        firstMaterial = loadedFile.materials[0]
        self.assertEqual(firstMaterial.get_material_game_version(), RSEGameVersions.RAINBOW_SIX, "Wrong material format detected")
        self.assertEqual(firstMaterial.versionNumber, 1, "Wrong material version number")
        self.assertEqual(firstMaterial.materialName, "WI_plain5", "Wrong material name")
        self.assertEqual(firstMaterial.textureName, "Wl_paper_congo_tan_leaves1.BMP", "Wrong texture name")

        self.assertAlmostEqual(firstMaterial.opacity, 1.0, 3, "Wrong opacity value")
        self.assertAlmostEqual(firstMaterial.emissiveStrength, 0.0, 3, "Wrong emissive strength value")
        self.assertEqual(firstMaterial.textureAddressMode, 3, "Wrong texture address mode value")
        self.assertEqual(firstMaterial.ambientColorUInt, [25, 25, 25], "Wrong ambient color")
        self.assertEqual(firstMaterial.diffuseColorUInt, [255, 255, 255], "Wrong diffuse color")
        self.assertEqual(firstMaterial.specularColorUInt, [229, 229, 229], "Wrong specular color")
        self.assertEqual(firstMaterial.normalizedColors, False, "Incorrectly determined whether colors are normalized in the file")
        self.assertAlmostEqual(firstMaterial.specularLevel, 0.0, 3, "Wrong specular value")
        self.assertEqual(firstMaterial.twoSided, False, "Wrong two sided material flag value")



if __name__ == '__main__':
    unittest.main()
