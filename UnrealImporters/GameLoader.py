import os

from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.R6MissionReader import R6MissionFile

class GameLoader(object):
    """Loads an RSE game and allows interaction"""
    # constructor adding a component
    def begin_play(self):
        print("Testing game loader")
        self.game_loader = RSEGameLoader()
        self.game_loader.load_game("D:/R6Data/FullGames/R6EWCD")

    def list_missions(self):
        print("listing missions")
        missions = self.game_loader.get_mission_list()
        for missionName in missions:
            self.uobject.PrintMission(missionName)

    def load_mission(self, missionName):
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


    def tick(self, delta_time):
        """Called every frame"""
        pass
