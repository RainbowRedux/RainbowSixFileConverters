import json

def load_settings(filename="settings.json"):
    settingsFile = open(filename)
    settings = json.load(settingsFile)
    settingsFile.close()
    return settings