"""Classes and functions to load and parse Mission files from Rainbow Six"""
from RainbowFileReaders import R6Settings
from FileUtilities.TextFileUtilities import read_tokenized_text_file, read_keyword_list

class R6MissionFile(object):
    """Mission description file for Rainbow Six"""
    def __init__(self):
        super(R6MissionFile, self).__init__()
    
    def read_room_list(self, keywords):
        room_list = []        
        nextKeyword = keywords[0]
        while nextKeyword != "End":
            room_list.append(keywords.pop(0))
            nextKeyword = keywords[0]
        #Discard the "End" keyword
        keywords.pop(0)
        return room_list

    def load_mission(self, path):
        pass

        self.filepath = path
        keywords = read_tokenized_text_file(path)

        self.map_file_name = keywords.pop(0)
        self.map_directory = keywords.pop(0)
        self.mission_name = keywords.pop(0)
        self.default_plan_filename = keywords.pop(0)
        self.briefing_filename = keywords.pop(0)
        self.debrief_filename = keywords.pop(0)
        self.mission_picture_filename = keywords.pop(0)

        self.render_hardware_near_clip = float(keywords.pop(0).replace("f",""))
        self.render_hardware_far_clip = float(keywords.pop(0).replace("f",""))
        self.render_software_near_clip = float(keywords.pop(0).replace("f",""))
        self.render_software_far_clip = float(keywords.pop(0).replace("f",""))

        self.render_fog_enabled = int(keywords.pop(0)
        self.render_fog_color = []
        for _ in range(3):
            self.render_fog_color.append(int(keywords.pop(0)))
        self.render_fog_start_distance = float(keywords.pop(0).replace("f",""))
        self.render_fog_end_distance = float(keywords.pop(0).replace("f",""))

        self.render_ambient_light_color = []
        for _ in range(3):
            self.render_ambient_light_color.append(int(keywords.pop(0)))
        self.render_background_color = []
        for _ in range(3):
            self.render_background_color.append(int(keywords.pop(0)))

        self.clouds_enabled = keywords.pop(0)
        self.clouds_texture_filename = keywords.pop(0)
        self.clouds_texture_multiplier = float(keywords.pop(0).replace("f",""))
        self.clouds_speed_multiplier = float(keywords.pop(0).replace("f",""))

        outdoorRoomsKeyword = keywords.pop(0)
        if outdoorRoomsKeyword != "OutdoorRooms":
            raise ValueError("OutdoorRooms keyword expected but not found. Found: " + str(outdoorRoomsKeyword))
            return

        self.outdoor_rooms = self.read_room_list(keywords)

        fogRoomsKeyword = keywords.pop(0)
        if fogRoomsKeyword != "FogRooms":
            raise ValueError("FogRooms keyword expected but not found. Found: " + str(fogRoomsKeyword))
            return

        self.fog_rooms = self.read_room_list(keywords)

        #TODO: Read background colors list and onwards
