"""Test reading RSB images from Rainbow Six (1998)"""
import logging
import unittest
from os import path

from Settings import load_settings
from RainbowFileReaders import CXPMaterialPropertiesReader

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.CRITICAL)

class R6RSBTests(unittest.TestCase):
    """Test reading R6 CXP files"""

    def test_original_cxp(self):
        """Tests reading the CXP file from the original game"""

        settings = load_settings(TEST_SETTINGS_FILE)

        CXPpath =  path.join(settings["gamePath_R6"], "data", "texture", "Sherman.CXP")

        loadedCXPDefs = CXPMaterialPropertiesReader.read_cxp(CXPpath)

        # 294 manually verified in TXT file
        self.assertEqual(len(loadedCXPDefs), 294, "Unexpected number of definitions in CXP File")


    def test_eagle_watch_cxp(self):
        """Tests reading the CXP file from eagle watch"""

        settings = load_settings(TEST_SETTINGS_FILE)

        CXPpath =  path.join(settings["gamePath_R6_EW"], "data", "texture", "Sherman.CXP")

        loadedCXPDefs = CXPMaterialPropertiesReader.read_cxp(CXPpath)

        # 395 manually verified in TXT file
        self.assertEqual(len(loadedCXPDefs), 395, "Unexpected number of definitions in CXP File")
