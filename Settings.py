import json

def load_settings():
    settingsFile = open("settings.json")
    settings = json.load(settingsFile)
    settingsFile.close()
    return settings