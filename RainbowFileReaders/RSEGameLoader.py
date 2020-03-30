"""Contains utility class to load a game from a directory and load/calculate associated settings, parameters and find resources"""

import os

from RainbowFileReaders.R6Constants import RSEEngineVersions, RSEGameVersions
from FileUtilities.DirectoryProcessor import gather_files_in_path

class RSEGameLoader(object):
    """Utility class to load a game from a directory and load/calculate associated settings, parameters and find resources"""
    def __init__(self):
        super(RSEGameLoader, self).__init__()

        self.game_path = ""
        self.game_name = ""
        self.game_version = RSEGameVersions.UNKNOWN
        self.engine_version = RSEEngineVersions.UNKNOWN
        self.mods = {}

    def load_game(self, path):
        """
        Loads a game from the given path. Will determine engine version and determine mods available (if available)
        Returns True if it was able to identify the game version
        """
        if os.path.isdir(path) is False:
            return False

        self.game_path = path
        self._determine_game_from_exes()

        if self.game_version is RSEGameVersions.UNKNOWN:
            return False
        return True

    def _determine_game_from_exes(self):
        if not self.game_path:
            return RSEGameVersions.UNKNOWN

        exes = [file for file in os.listdir(self.game_path) if file.lower().endswith(".exe")]

        # Rainbow Six
        if "RainbowSix.exe" in exes:
            #TODO: Read this from Constants.txt
            self.game_name = "Rainbow Six"
            self.game_version = RSEGameVersions.RAINBOW_SIX
            self.engine_version = RSEEngineVersions.SHERMAN
            if "RainbowSixMP.exe" in exes:
                # Add Eagle Watch as a mod even though it doesn't work like ROMMEL mods
                self.mods["Eagle Watch"] = "."

        RogueSpearGameExes = ["CovertOperations.exe", "RogueSpear.exe", "BlackThorn.exe", "UrbanOperations.exe"]

        for exeName in RogueSpearGameExes:
            if exeName in exes:
                self.game_version = RSEGameVersions.ROGUE_SPEAR
                self.engine_version = RSEEngineVersions.ROMMEL
                #TODO: determine game name
                self.game_name = "Rogue Spear"

        return self.game_version

    def get_mission_list(self):
        """
        Returns a list of missions that are avaible in the current game and loaded mods
        """
        mission_paths = gather_files_in_path(".MIS", self.game_path)
        if "Eagle Watch" in self.mods:
            mp_mission_paths = gather_files_in_path(".MPS", self.game_path)
            mission_paths = mission_paths + mp_mission_paths


        missions = {}
        for mission_path in mission_paths:
            mission_filename = os.path.basename(mission_path)
            mission_code = os.path.splitext(mission_filename)[0]
            missions[mission_code] = mission_path
        return missions

    def get_map_list(self):
        """
        Returns a lost of maps available in the current game
        """
        map_paths = gather_files_in_path(".MAP", self.game_path)

        maps = {}
        for map_path in map_paths:
            map_filename = os.path.basename(map_path)
            map_code = os.path.splitext(map_filename)[0]
            maps[map_code] = map_path
        return maps

    def get_mod_list(self):
        """
        Returns a list of mods available in the current game
        """
        #TODO: read mods in Rogue Spear games
        return list(self.mods.keys())

    def load_mod(self, mod_name):
        """
        Loads the specified name and allows resources belonging to the mod to be retrieved
        """
        #TODO: load a mod

    def print_game_info(self):
        """
        Prints information about the currently loaded game
        """
        print("Game Path = " + self.game_path)
        print("Game Name = " + self.game_name)
        print("Game Version = " + self.game_version)
        print("EngineVersion = " + self.engine_version)

        maps = self.get_map_list()
        print("Map list:")
        for mapCode, mapPath in maps.items():
            print("\t" + str(mapCode) + " : " + str(mapPath))

        missions = self.get_mission_list()
        print("Mission list:")
        for missionCode, missionPath in missions.items():
            print("\t" + str(missionCode) + " : " + str(missionPath))


def test_game_path(path):
    """Test function to load a specific directory and display information"""
    print("===============================")
    print("Loading new game directory: " + path)
    print("===============================")
    game = RSEGameLoader()
    game.load_game(path)
    game.print_game_info()

if __name__ == "__main__":
    test_game_path("D:/R6Data/FullGames/R6EWCD")
    test_game_path("D:/R6Data/FullGames/RSUOCOCD")
