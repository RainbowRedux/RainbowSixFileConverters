"""Contains all functions to do with loading a game, such as finding the exe, listing missions, and loading missions"""
import os
import logging
from pathlib import Path

import tkinter as tk
from tkinter import filedialog

from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.R6MissionReader import R6MissionFile

log = logging.getLogger(__name__)

class GameLoader(object):
    """Loads an RSE game and allows interaction"""

    def ask_exe_file(self):
        """Prompts the user to find their R6 exe file"""

        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(title="Select your game exe file",filetypes = (("Executable","*.exe"),("all files","*.*")))

        if file_path.lower().endswith("exe"):
            log.debug("Found rainbowsix executable")
            p = Path(file_path)
            file_path = p.parent

        return file_path

    # constructor adding a component
    def begin_play(self):
        """Run on spawn, or on game start"""
        log.debug("Testing game loader")
        self.game_loader = RSEGameLoader()
        file_path = self.ask_exe_file()
        if not file_path:
            file_path = "D:/R6Data/FullGames/R6EWCD"

        log.info('Using gamepath: %s', file_path)
        self.game_loader.load_game(file_path)

        self.list_missions()
        self.uobject.PresentMenu()

    def list_missions(self):
        """Passes the missions through to the unreal class"""
        log.debug("listing missions")
        missions = self.game_loader.get_mission_list()
        for missionName in missions:
            self.uobject.PrintMission(missionName)

    def load_mission(self, missionName):
        """Loads a mission file and sets appropriate parameters"""
        missions = self.game_loader.get_mission_list()
        missionPath = missions[missionName]
        if missionPath is not None:
            missionFile = R6MissionFile()
            missionFile.load_mission(missionPath)
            mappath = os.path.join(self.game_loader.game_path, "data", "map", missionFile.map_directory, missionFile.map_file_name)
            mappath = os.path.normpath(mappath)
            self.uobject.LoadMap(mappath)
            self.uobject.LoadedMap.SetFogParameters(missionFile.render_fog_color[0], missionFile.render_fog_color[1], missionFile.render_fog_color[2], missionFile.render_fog_start_distance, missionFile.render_fog_end_distance)
            if missionFile.render_fog_enabled != 0:
                self.uobject.LoadedMap.SetFogEnabled(True)
            else:
                self.uobject.LoadedMap.SetFogEnabled(False)
            self.uobject.LoadedMap.SetAmbientLightColor(missionFile.render_ambient_light_color[0], missionFile.render_ambient_light_color[1], missionFile.render_ambient_light_color[2])
            self.uobject.LoadedMap.SetSkyColor(missionFile.render_background_color[0], missionFile.render_background_color[1], missionFile.render_background_color[2])


    def tick(self, delta_time):
        """Called every frame"""
