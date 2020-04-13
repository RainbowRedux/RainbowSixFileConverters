"""Provides a simple interface to load a settings file"""
import json

def load_settings(filename="settings.json"):
    """Loads a json file that contains the settings desired"""
    settingsFile = open(filename)
    settings = json.load(settingsFile)
    settingsFile.close()
    return settings
