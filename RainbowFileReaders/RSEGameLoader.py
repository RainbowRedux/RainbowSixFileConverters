from RainbowFileReaders import R6Constants
from RainbowFileReaders.R6Constants import RSEEngineVersions
class RSEGameLoader(object):
    def __init__(self):
        super(RSEGameLoader, self).__init__()

        self.game_path = ""
        self.game_name = ""
        self.engine_version = RSEEngineVersions.UNKNOWN

    def load_game(self, path):
        pass
    
    def list_missions(self):
        pass

    def list_maps(self):
        pass

    def list_mods(self):
        pass
    
    def load_mod(self, mod_name):
        pass