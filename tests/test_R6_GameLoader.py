"""Tests the RSEGameLoader module with Rainbow Six (1998)"""

import logging
import unittest

from FileUtilities.Settings import load_settings
from RainbowFileReaders import RSEGameLoader
from RainbowFileReaders.R6Constants import RSEEngineVersions, RSEGameVersions

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.CRITICAL)

class R6MAPTests(unittest.TestCase):
    """Test Gameloader on Rainbow Six (1998)"""

    def test_eagle_watch_detection(self):
        """Tests recognising Eagle Watch"""
        settings = load_settings(TEST_SETTINGS_FILE)

        eagleWatchGame = RSEGameLoader.RSEGameLoader()
        loadedGameSuccessfully = eagleWatchGame.load_game(settings["gamePath_R6_EW"])
        self.assertTrue(loadedGameSuccessfully, "Failed to load game with Eagle Watch")
        self.assertEqual(eagleWatchGame.get_mod_list(), ["Eagle Watch"], "Failed to detect eagle watch")

        normalGame = RSEGameLoader.RSEGameLoader()
        loadedGameSuccessfully = normalGame.load_game(settings["gamePath_R6"])
        self.assertTrue(loadedGameSuccessfully, "Failed to load original game")
        self.assertEqual(normalGame.get_mod_list(), [], "Detected a mod where there shouldn't be one")

    def test_game_detection(self):
        """Tests recognising Rainbow Six"""
        settings = load_settings(TEST_SETTINGS_FILE)

        invalidGame = RSEGameLoader.RSEGameLoader()
        loadedGameSuccessfully = invalidGame.load_game("/ThisPathWillNEverWork/")
        self.assertFalse(loadedGameSuccessfully, "Incorrectly reported that an invalid game loaded")

        normalGame = RSEGameLoader.RSEGameLoader()
        loadedGameSuccessfully = normalGame.load_game(settings["gamePath_R6"])
        self.assertTrue(loadedGameSuccessfully, "Failed to load original game")

        self.assertEqual(normalGame.game_name, "Rainbow Six", "Didn't recognise game name")
        self.assertEqual(normalGame.game_version, RSEGameVersions.RAINBOW_SIX, "Didn't recognise game version")
        self.assertEqual(normalGame.engine_version, RSEEngineVersions.SHERMAN, "Didn't recognise engine version")
