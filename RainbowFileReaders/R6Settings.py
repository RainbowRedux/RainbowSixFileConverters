"""This file stores constants and settings related to R6 files and directory formats.
This also contains a few functions to determine some relevant settings such as game installation directory """
import os
from typing import Tuple, Optional, List

paths = {}
#R6 and onwards
#These were retrieved and modified from Win32 Registry entries
#These are all relative to data path
paths["ActorPath"] = "actor"
paths["BiographyTextPath"] = "text\\bios"
paths["BitmapPath"] = "bitmap"
paths["BriefingBitmapPath"] = "shell\\briefing"
paths["BriefingTextPath"] = "text\\briefing"
paths["CursorPath"] = "shell\\cursor"
paths["DialoguePath"] = "dialogue"
paths["EquipmentPath"] = "kit"
paths["EquipTextPath"] = "text\\kit"
paths["FacesPath"] = "shell\\faces"
paths["FontPath"] = "font"
paths["GamePath"] = "save"
paths["IconPath"] = "icon"
paths["InstallationPath"] = "d:\\goggames\\tom clancys rainbow six\\"
paths["IntelBitmapPath"] = "shell\\intel"
paths["IntelTextPath"] = "text\\intel"
paths["JournalPath"] = "journals"
paths["MissionPath"] = "mission"
paths["MissionSplashPath"] = "text\\splash"
paths["MissionTextPath"] = "text\\mission"
paths["ModelPath"] = "model"
paths["MotionPath"] = "motion"
paths["PlanPath"] = "plan"
paths["PlotPath"] = "plot"
paths["ProfileTextPath"] = "text\\profile"
paths["RosterBitmapPath"] = "shell\\roster"
paths["ShellTextPath"] = "text\\interface"
paths["TempPath"] = "temp"
paths["TextPath"] = "text"
paths["TexturePath"] = "texture"
paths["SoundPath"] = "sound"
paths["CharacterPath"] = "character"
paths["MapPath"] = "map"
paths["MissionSplashBMPPath"] = "Splash"
paths["BriefingSoundPath"] = "sound"
paths["ActionMusicPath"] = "sound\\music"
paths["VideoPath"] = "video"


#Rogue Spear only
paths["InstallationPath"] = ""
paths["ArmPatchPath"] = "armpatch"
paths["ReplayPath"] = "replay"
paths["MissionSplashBitmapPath"] = "splash"
paths["DataPath"] = "data"
paths["ModsPath"] = "mods"
paths["UserPath"] = ""

def determine_data_paths_for_file(filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Takes the path of the file currently being processed, and will identify the base game path, and if applicable, the current mod.
    It assumes a file is being loaded from an installed game directory, installed as a full install. Not tested on partial installs, and CDs.
    If any path cannot be determined, it will be returned as None.
    All relative paths will be returned as absolute paths, which can be reversed with os.path.relpath()
    @returns Tuple of (BaseGamePath, BaseDataPath, ModPath)
    """

    #Get the absolute path
    absPath = os.path.abspath(filename)
    absPath = os.path.normpath(absPath)
    #Base game path
    gamePath = None
    modName = None
    currDirParent = absPath
    prevDir = None
    while gamePath is None:
        currDirParent, currDir = os.path.split(currDirParent)
        if currDir is None or currDir == "":
            break
        if currDir == paths["DataPath"]:
            gamePath = currDirParent
        elif currDir == paths["ModsPath"]:
            gamePath = currDirParent
            modName = prevDir
        prevDir = currDir

    baseDataPath = None
    modPath = None
    if gamePath is not None:
        baseDataPath = os.path.join(gamePath, paths["DataPath"])
        if modName is not None:
            modPath = os.path.join(gamePath, paths["ModsPath"], modName)

    return (gamePath, baseDataPath, modPath)

def get_relevant_global_texture_paths(filename: str) -> List[str]:
    """Returns a list of paths that are used as global texture paths in RSE games.
    Expects a full filepath to be passed in which can then be used for searching for the appropriate folders"""
    filepath = os.path.dirname(filename)
    filepath = os.path.normpath(filepath)
    texturePaths: List[str] = []
    texturePaths.append(filepath)
    dataPaths = determine_data_paths_for_file(filename)[1:]
    for path in dataPaths:
        if path is not None:
            texturePaths.append(os.path.join(path, paths["TexturePath"]))
    #As a last resort, add the map folders to search, resolves a few missing textures
    if filename.lower().endswith(".map"):
        for path in dataPaths:
            if path is not None:
                texturePaths.append(os.path.join(path, paths["MapPath"]))

    return texturePaths

def restore_original_texture_name(filename: str) -> str:
    """Create original texture name from RSB filename"""
    newfilename = filename
    if filename.startswith("TGA"):
        #Strip TGA from front of filename
        newfilename = filename[3:]
        newfilename = newfilename[:-4] + ".tga"
    else:
        newfilename = newfilename[:-4] + ".bmp"
    return newfilename

def get_rsb_texture_name(filename: str) -> str:
    """Match source texture names to RSB texture names that were shipped"""
    ext = filename.lower()[-4:]
    newfilename = filename
    if ext in (".bmp", ".tga"):
        #Replace extension with .RSB
        newfilename = newfilename[:-4]
        newfilename += ".RSB"
        if ext == ".tga":
            #Append TGA to front of filename
            newfilename = "TGA" + newfilename
    return newfilename

def find_texture(filename: str, dataPath: str) -> Optional[str]:
    """Looks for a texture using the source name in the path.
    Will perform texture name fixups to match new names"""
    if filename.lower() == "null":
        return None
    newfilename = get_rsb_texture_name(filename)
    result = None
    for root, dirs, files in os.walk(dataPath):
        for name in files:
            # Compare lowercase versions since windows is case-insensitive
            if name.lower() == newfilename.lower():
                result = os.path.join(root, name)

        for name in dirs:
            pass
    return result
