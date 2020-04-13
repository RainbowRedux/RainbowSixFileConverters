"""A quick sample program to try loading games and listing missions"""

import logging

from RainbowFileReaders.RSEGameLoader import RSEGameLoader
from RainbowFileReaders.R6MissionReader import R6MissionFile
from FileUtilities.Settings import load_settings

log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    settings = load_settings()
    game = RSEGameLoader()
    game.load_game(settings["gamePath"])
    game.print_game_info()

    missions = game.get_mission_list()

    for _, missionPath in missions.items():
        mission = R6MissionFile()
        log.info("Loading: %s", missionPath)
        mission.load_mission(missionPath)

        log.info("Hardware far clip: %f", mission.render_hardware_far_clip)
        log.info("List of rooms with fog:")
        for fogroom in mission.fog_rooms:
            log.info("\t- %s", fogroom)
