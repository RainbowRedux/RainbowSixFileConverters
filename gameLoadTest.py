from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.R6MissionReader import R6MissionFile

if __name__ == "__main__":
    game = RSEGameLoader()
    game.load_game("D:/R6Data/FullGames/R6EWCD")
    game.print_game_info()

    missions = game.get_mission_list()

    for _, missionPath in missions.items():
        mission = R6MissionFile()
        print("Loading: " + missionPath)
        mission.load_mission(missionPath)

        print(mission.render_hardware_far_clip)
        for fogroom in mission.fog_rooms:
            print(fogroom)
