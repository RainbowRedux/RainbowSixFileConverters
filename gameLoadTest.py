"""A quick sample program to try loading games and listing missions"""

from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.R6MissionReader import R6MissionFile
from FileUtilities.Settings import load_settings

if __name__ == "__main__":
    settings = load_settings()
    game = RSEGameLoader()
    game.load_game(settings["gamePath"])
    game.print_game_info()

    missions = game.get_mission_list()

    for _, missionPath in missions.items():
        mission = R6MissionFile()
        print("Loading: " + missionPath)
        mission.load_mission(missionPath)

        print(mission.render_hardware_far_clip)
        for fogroom in mission.fog_rooms:
            print(fogroom)
