"""Test reading RSB images from Rainbow Six (1998)"""
import logging
import unittest

from RainbowFileReaders.R6Settings import determine_data_paths_for_file

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.INFO)

class R6SettingsTests(unittest.TestCase):
    """Test Module and functionality associated with R6 game settings and path determination"""

    def test_rs_demo_path(self):
        """Tests a map path from the rogue spear demo"""
        #A path that should work, with no mod
        paths = determine_data_paths_for_file("../Data/Test/ReducedGames/RSDemo/data/map/rm01/rm01.map")
        self.assertEqual(paths[0][-6:], "RSDemo", "Failed to identify base game path")
        self.assertEqual(paths[1][-4:], "data", "Failed to identify base game data path")
        self.assertEqual(paths[2], None, "Incorrectly identified mod")

    def test_rs_mod_path(self):
        """Tests a path from a rogue spear mod"""
        #A path that should work, with a mod
        paths = determine_data_paths_for_file("../Data/Test/ReducedGames/RSDemo/mods/CLASSIC MISSIONS/map/cl01/cl01.map")
        self.assertEqual(paths[0][-6:], "RSDemo", "Failed to identify base game path")
        self.assertEqual(paths[1][-4:], "data", "Failed to identify base game data path")
        self.assertEqual(paths[2][-16:], "CLASSIC MISSIONS", "Incorrectly identified mod")

    def test_r6_path(self):
        """Tests a path from rainbow six"""
        #A path that should work, with no mod
        paths = determine_data_paths_for_file("../Data/Test/ReducedGames/R6GOG/data/map/m01/M01.map")
        self.assertEqual(paths[0][-5:], "R6GOG", "Failed to identify base game path")
        self.assertEqual(paths[1][-4:], "data", "Failed to identify base game data path")
        self.assertEqual(paths[2], None, "Incorrectly identified mod")
    def test_bad_path(self):
        """Tests an invalid path"""
        #A path that should not work, as it will be unable to determine directory structure
        paths = determine_data_paths_for_file("../Rainbow")
        self.assertEqual(paths[0], None, "Incorrectly identified base game path when none exists")
        self.assertEqual(paths[1], None, "Incorrectly identified base game data path")
        self.assertEqual(paths[2], None, "Incorrectly identified mod")
