"""Contains utility class to load a game from a directory and load/calculate associated settings, parameters and find resources"""

import logging
import os

from RainbowFileReaders.R6Constants import RSEEngineVersions, RSEGameVersions
from FileUtilities.DirectoryProcessor import gather_files_in_path

log = logging.getLogger(__name__)

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
        log.info("Game Path = %s", self.game_path)
        log.info("Game Name = %s", self.game_name)
        log.info("Game Version = %s", self.game_version)
        log.info("EngineVersion = %s", self.engine_version)

        maps = self.get_map_list()
        log.info("Map list:")
        for mapCode, mapPath in maps.items():
            log.info("\t%s : %s", mapCode, mapPath)

        missions = self.get_mission_list()
        log.info("Mission list:")
        for missionCode, missionPath in missions.items():
            log.info("\t%s : %s", missionCode, missionPath)
