"""Test reading RSB images from Rainbow Six (1998)"""
import logging
import unittest
from os import path

from PIL import Image

from FileUtilities.Settings import load_settings
from FileUtilities.MipMapGenerator import generate_mip_maps
from RainbowFileReaders import RSBImageReader

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.CRITICAL)

class R6RSBTests(unittest.TestCase):
    """Test R6 RSBs"""

    def test_mip_map_generation(self):
        """Tests reading an image that contains a palette"""
        settings = load_settings(TEST_SETTINGS_FILE)

        RSB_filepath = path.join(settings["gamePath_R6_EW"], "data", "texture", "08_engine.RSB")

        loadedFile = RSBImageReader.RSBImageFile()
        readSucessfullyToEOF = loadedFile.read_file(RSB_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        fullColorImage = loadedFile.convert_full_color_image()

        mips = generate_mip_maps(fullColorImage)

        self.assertEqual(len(mips), 8, "Failed to generate correct number of mipmaps")

    def test_impossible_mip_map_generation(self):
        settings = load_settings(TEST_SETTINGS_FILE)

        RSB_filepath = path.join(settings["gamePath_R6_EW"], "data", "shell", "briefing", "Ac_a13.RSB")

        loadedFile = RSBImageReader.RSBImageFile()
        readSucessfullyToEOF = loadedFile.read_file(RSB_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        fullColorImage = loadedFile.convert_full_color_image()

        mips = generate_mip_maps(fullColorImage)

        self.assertIsNone(mips, "Did not return None, instead generated mip-maps")

    def test_palette_image(self):
        """Tests reading an image that contains a palette"""
        settings = load_settings(TEST_SETTINGS_FILE)

        RSB_filepath = path.join(settings["gamePath_R6_EW"], "data", "texture", "08_engine.RSB")

        loadedFile = RSBImageReader.RSBImageFile()
        readSucessfullyToEOF = loadedFile.read_file(RSB_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        self.assertEqual(loadedFile.header.width, 128, "Unexpected image width")

        self.assertEqual(loadedFile.header.height, 128, "Unexpected image height")

        self.assertEqual(loadedFile.header.containsPalette, 1, "Did not detect palette in image which contains a palette")

        paletteImage = loadedFile.convert_palette_image()

        self.assertEqual(paletteImage.width, loadedFile.header.width, "Widths do not match on palette image")

        self.assertEqual(paletteImage.height, loadedFile.header.height, "Heights do not match on palette image")

        fullColorImage = loadedFile.convert_full_color_image()

        self.assertEqual(fullColorImage.width, loadedFile.header.width, "Widths do not match on full color image")

        self.assertEqual(fullColorImage.height, loadedFile.header.height, "Heights do not match on full color image")

    def test_full_color_image(self):
        """Tests reading an image that does not contain a palette"""
        settings = load_settings(TEST_SETTINGS_FILE)

        RSB_filepath = path.join(settings["gamePath_R6_EW"], "data", "shell", "briefing", "Ac_a13.RSB")

        loadedFile = RSBImageReader.RSBImageFile()
        readSucessfullyToEOF = loadedFile.read_file(RSB_filepath)

        self.assertTrue(readSucessfullyToEOF, "Failed to read whole file")

        self.assertEqual(loadedFile.header.width, 38, "Unexpected image width")

        self.assertEqual(loadedFile.header.height, 46, "Unexpected image height")

        self.assertEqual(loadedFile.header.containsPalette, 0, "Detected palette in image that does not contain a palette")

        fullColorImage = loadedFile.convert_full_color_image()

        self.assertEqual(fullColorImage.width, loadedFile.header.width, "Widths do not match on full color image")

        self.assertEqual(fullColorImage.height, loadedFile.header.height, "Heights do not match on full color image")

if __name__ == '__main__':
    unittest.main()
