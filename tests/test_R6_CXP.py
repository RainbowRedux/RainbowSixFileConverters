"""Test reading RSB images from Rainbow Six (1998)"""
import logging
import unittest
from os import path

from FileUtilities.Settings import load_settings
from RainbowFileReaders import CXPMaterialPropertiesReader

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.CRITICAL)

class R6CXPTests(unittest.TestCase):
    """Test reading R6 CXP files"""

    def test_original_cxp(self):
        """Tests reading the CXP file from the original game"""

        settings = load_settings(TEST_SETTINGS_FILE)

        CXPpath =  path.join(settings["gamePath_R6"], "data", "texture", "Sherman.CXP")

        manuallyLoadedCXPDefs = CXPMaterialPropertiesReader.read_cxp(CXPpath)

        # 294 manually verified in TXT file
        self.assertEqual(len(manuallyLoadedCXPDefs), 294, "Unexpected number of definitions in manually loaded CXP File")

        CXPpath =  path.join(settings["gamePath_R6"], "data")

        autoLoadedCXPDefs = CXPMaterialPropertiesReader.load_relevant_cxps(CXPpath)
        self.assertEqual(len(autoLoadedCXPDefs), 294, "Unexpected number of definitions in Auto loaded CXP File")


    def test_eagle_watch_cxp(self):
        """Tests reading the CXP file from eagle watch"""

        settings = load_settings(TEST_SETTINGS_FILE)

        CXPpath =  path.join(settings["gamePath_R6_EW"], "data", "texture", "Sherman.CXP")

        manuallyLoadedCXPDefs = CXPMaterialPropertiesReader.read_cxp(CXPpath)

        # 395 manually verified in TXT file
        self.assertEqual(len(manuallyLoadedCXPDefs), 395, "Unexpected number of definitions in CXP File")

        CXPpath =  path.join(settings["gamePath_R6_EW"], "data")

        autoLoadedCXPDefs = CXPMaterialPropertiesReader.load_relevant_cxps(CXPpath)
        self.assertEqual(len(autoLoadedCXPDefs), 395, "Unexpected number of definitions in Auto loaded CXP File")
