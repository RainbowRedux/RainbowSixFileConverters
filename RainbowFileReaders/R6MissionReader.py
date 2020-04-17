"""Classes and functions to load and parse Mission files from Rainbow Six"""
from typing import List

from FileUtilities.TextFileUtilities import read_tokenized_text_file

class R6MissionFile(object):
    """Mission description file for Rainbow Six"""
    def __init__(self):
        super(R6MissionFile, self).__init__()

    def read_room_list(self, keywords: List[str]) -> List[str]:
        """Will read a list of rooms until the 'End' keyword is found"""
        room_list: List[str] = []
        nextKeyword = keywords[0]
        while nextKeyword != "End":
            room_list.append(keywords.pop(0))
            nextKeyword = keywords[0]
        #Discard the "End" keyword
        keywords.pop(0)
        return room_list

    def load_mission(self, path: str):
        """Reads all mission properties from a .MIS or .MPS file"""
        self.filepath: str = path
        keywords = read_tokenized_text_file(path)

        self.map_file_name: str = keywords.pop(0)
        self.map_directory: str = keywords.pop(0)
        self.mission_name: str = keywords.pop(0)
        self.default_plan_filename: str = keywords.pop(0)
        self.briefing_filename: str = keywords.pop(0)
        self.debrief_filename: str = keywords.pop(0)
        self.mission_picture_filename: str = keywords.pop(0)

        self.render_hardware_near_clip: float = float(keywords.pop(0).replace("f",""))
        self.render_hardware_far_clip: float = float(keywords.pop(0).replace("f",""))
        self.render_software_near_clip: float = float(keywords.pop(0).replace("f",""))
        self.render_software_far_clip: float = float(keywords.pop(0).replace("f",""))

        self.render_fog_enabled: int = int(keywords.pop(0))
        self.render_fog_color: List[int] = []
        for _ in range(3):
            self.render_fog_color.append(int(keywords.pop(0)))
        self.render_fog_start_distance: float = float(keywords.pop(0).replace("f",""))
        self.render_fog_end_distance: float = float(keywords.pop(0).replace("f",""))

        self.render_ambient_light_color: List[int] = []
        for _ in range(3):
            self.render_ambient_light_color.append(int(keywords.pop(0)))
        self.render_background_color: List[int] = []
        for _ in range(3):
            self.render_background_color.append(int(keywords.pop(0)))

        clouds_enabled_raw: str = keywords.pop(0)
        self.clouds_enabled: bool = False
        if clouds_enabled_raw == "1":
            self.clouds_enabled = True
        self.clouds_texture_filename: str = keywords.pop(0)
        self.clouds_texture_multiplier: float = float(keywords.pop(0).replace("f",""))
        self.clouds_speed_multiplier: float = float(keywords.pop(0).replace("f",""))

        outdoorRoomsKeyword: str = keywords.pop(0)
        if outdoorRoomsKeyword != "OutdoorRooms":
            raise ValueError("OutdoorRooms keyword expected but not found. Found: " + str(outdoorRoomsKeyword))

        self.outdoor_rooms: List[str] = self.read_room_list(keywords)

        fogRoomsKeyword: str = keywords.pop(0)
        if fogRoomsKeyword != "FogRooms":
            raise ValueError("FogRooms keyword expected but not found. Found: " + str(fogRoomsKeyword))

        self.fog_rooms: List[str] = self.read_room_list(keywords)

        #TODO: Read background colors list and onwards
