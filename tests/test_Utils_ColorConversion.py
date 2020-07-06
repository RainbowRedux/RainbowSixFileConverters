"""Test Color Conversion utilities"""
import logging
import unittest
import random

from FileUtilities import ColorConversionUtilities
from FileUtilities.Settings import load_settings

TEST_SETTINGS_FILE = "test_settings.json"

logging.basicConfig(level=logging.CRITICAL)

class UtilsColorConversionTests(unittest.TestCase):
    """Test Color Conversion utilities"""

    def test_max_colors(self):
        """ Tests both lookup and brute force methods with white (maximum) colors in ARGB_0565 and ARGB_4444 formats """

        max_color_0565_brute = ColorConversionUtilities.read_bitmask_ARGB_color(65535, 5, 6, 5, 0)
        max_color_4444_brute = ColorConversionUtilities.read_bitmask_ARGB_color(65535, 4, 4, 4, 4)

        max_color_0565_lookup = ColorConversionUtilities.COLOR_LOOKUPS[ColorConversionUtilities.ColorFormats.CF_ARGB_0565][65535]
        max_color_4444_lookup = ColorConversionUtilities.COLOR_LOOKUPS[ColorConversionUtilities.ColorFormats.CF_ARGB_4444][65535]

        self.assertEqual(max_color_0565_brute, max_color_0565_lookup, "Lookup and brute force color conversion methods don't match with ARGB_0565 format")
        self.assertEqual(max_color_4444_brute, max_color_4444_lookup, "Lookup and brute force color conversion methods don't match with ARGB_4444 format")

    def test_min_colors(self):
        """ Tests both lookup and brute force methods with black (minimum) colors in ARGB_0565 and ARGB_4444 formats """

        min_color_0565_brute = ColorConversionUtilities.read_bitmask_ARGB_color(0, 5, 6, 5, 0)
        min_color_4444_brute = ColorConversionUtilities.read_bitmask_ARGB_color(0, 4, 4, 4, 4)

        min_color_0565_lookup = ColorConversionUtilities.COLOR_LOOKUPS[ColorConversionUtilities.ColorFormats.CF_ARGB_0565][0]
        min_color_4444_lookup = ColorConversionUtilities.COLOR_LOOKUPS[ColorConversionUtilities.ColorFormats.CF_ARGB_4444][0]

        self.assertEqual(min_color_0565_brute, min_color_0565_lookup, "Lookup and brute force color conversion methods don't match with ARGB_0565 format")
        self.assertEqual(min_color_4444_brute, min_color_4444_lookup, "Lookup and brute force color conversion methods don't match with ARGB_4444 format")

    def test_random_colors_ARGB_0565(self):
        """ Tests both lookup and brute force methods with random colors in ARGB_0565 format """
        settings = load_settings(TEST_SETTINGS_FILE)

        for _ in range(settings["random_color_test_count"]):
            random_color = random.randint(0,65535)
            random_color_0565_brute = ColorConversionUtilities.read_bitmask_ARGB_color(random_color, 5, 6, 5, 0)
            random_color_0565_lookup = ColorConversionUtilities.COLOR_LOOKUPS[ColorConversionUtilities.ColorFormats.CF_ARGB_0565][random_color]
            self.assertEqual(random_color_0565_brute, random_color_0565_lookup, "Lookup and brute force color conversion methods don't match with ARGB_0565 format")

    def test_random_colors_ARGB_4444(self):
        """ Tests both lookup and brute force methods with random colors in ARGB_4444 format """
        settings = load_settings(TEST_SETTINGS_FILE)

        for _ in range(settings["random_color_test_count"]):
            random_color = random.randint(0,65535)
            random_color_4444_brute = ColorConversionUtilities.read_bitmask_ARGB_color(random_color, 4, 4, 4, 4)
            random_color_4444_lookup = ColorConversionUtilities.COLOR_LOOKUPS[ColorConversionUtilities.ColorFormats.CF_ARGB_4444][random_color]
            self.assertEqual(random_color_4444_brute, random_color_4444_lookup, "Lookup and brute force color conversion methods don't match with ARGB_4444 format")
