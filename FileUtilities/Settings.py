"""Provides a simple interface to load a settings file"""
import json

from typing import Dict, Any

def load_settings(filename="settings.json") -> Dict[str, Any]:
    """Loads a json file that contains the settings desired"""
    settingsFile = open(filename)
    settings = json.load(settingsFile)
    settingsFile.close()
    return settings
