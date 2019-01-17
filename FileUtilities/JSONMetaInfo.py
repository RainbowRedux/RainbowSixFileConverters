import json

class JSONMetaInfo(object):
    """Lazy wrapper to allow quick serialization of meta data"""

    def __init__(self):
        pass

    def setFilename(self, filename):
        self.filename = filename

    def add_info(self, key, info):
        self.__setattr__(key, info)

    def getJSON(self):
        return json.dumps(self, cls=CustomJSONEncoder)

    def writeJSON(self, filename):
        jsonString = json.dumps(self, cls=CustomJSONEncoder, indent=4)
        fp = open(filename, "w")
        fp.write(jsonString)
        fp.close()


class CustomJSONEncoder(json.JSONEncoder):
    """A quick and  dirty custom JSON encoder that allows serialization of custom objects"""
    # https://code.tutsplus.com/tutorials/serialization-and-deserialization-of-python-objects-part-1--cms-26183
    # disabled pylint E0202 because it is desired to hide the parent definition
    def default(self, o): # pylint: disable=E0202
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)
