"""Test reading SOB files from Rainbow Six (1998)"""
import logging
import unittest
from os import path

from FileUtilities.Settings import load_settings
from FileUtilities.DirectoryUtils import gather_files_in_path
from RainbowFileReaders import SOBModelReader

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.CRITICAL)

class R6SOBTests(unittest.TestCase):
    """Test R6 SOBs"""

    def check_section_strings(self, loadedSOBFile):
        """Check all strings in the mapFile are as expected"""
        self.assertEqual(loadedSOBFile.header.header_begin_message.string, "BeginModel")
        self.assertEqual(loadedSOBFile.materialListHeader.material_list_string.string, "MaterialList")
        self.assertEqual(loadedSOBFile.geometryListHeader.geometry_list_string.string, "GeometryList")

        self.assertEqual(loadedSOBFile.footer.end_model_string.string, "EndModel", "Unexpected end of map footer string")

    def test_R6_SOB_Structure(self):
        """Tests reading an R6 SOB file, specifically ak47.sob"""
        settings = load_settings(TEST_SETTINGS_FILE)

        sob_filepath = path.join(settings["gamePath_R6"], "data", "model", "ak47.sob")

        loadedFile = SOBModelReader.SOBModelFile()
        readSucessfullyToEOF = loadedFile.read_file(sob_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        self.check_section_strings(loadedFile)

        self.assertEqual(loadedFile.materialListHeader.numMaterials, 7, "Unexpected number of materials in header")

        self.assertEqual(len(loadedFile.materials), 7, "Unexpected number of materials read")

        self.assertEqual(loadedFile.materials[0].material_name.string, "aK barell", "Unexpected material name")

        self.assertEqual(loadedFile.materials[0].texture_name.string, "AK47_BARREL_32.BMP", "Unexpected material name")

        self.assertEqual(len(loadedFile.geometryObjects), 1, "Unexpected number of geometry objects")

        self.assertEqual(loadedFile.geometryObjects[0].name_string.string, "AK47", "Unexpected object name")

        self.assertEqual(loadedFile.geometryObjects[0].vertexCount, 81, "Unexpected number of vertices")

    def test_load_all_R6_SOBs(self):
        """Attempt to load and validate the sections of each map in the directory"""
        settings = load_settings(TEST_SETTINGS_FILE)

        discovered_files = gather_files_in_path(".SOB", settings["gamePath_R6_EW"])

        for sob_filepath in discovered_files:
            loadedFile = SOBModelReader.SOBModelFile()
            readSucessfullyToEOF = loadedFile.read_file(sob_filepath)

            self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

            self.check_section_strings(loadedFile)
