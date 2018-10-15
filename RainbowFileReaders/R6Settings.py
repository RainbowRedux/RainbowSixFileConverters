#This file stores constants and settings related to R6 files and directory formats

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


UINT_MAX = 4294967295