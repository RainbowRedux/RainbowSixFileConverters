from PIL import Image
import time
import DirectoryProcessor
import json

from RainbowFileReaders import MAPLevelReader
from FileWriters import JSONMetaInfo, OBJModelWriter
from RainbowFileReaders.R6Constants import RSEGameVersions

def convert_MAP(filename):
    print("Processing: " + filename)

    modelFile = MAPLevelReader.MAPLevelFile()
    modelFile.read_file(filename)

    #strip out lengthy data which is already being interpreted correctly to make it easier for humans to view the json file
    for geometryObject in modelFile.geometryObjects:
        geometryObject.vertices = []
        geometryObject.vertexParams = []
        geometryObject.faces = []
        if modelFile.gameVersion == RSEGameVersions.RAINBOW_SIX:
            for mesh in geometryObject.meshes:
                mesh.faceIndices = []

    meta = JSONMetaInfo.JSONMetaInfo()
    meta.add_info("filecontents", modelFile)
    meta.add_info("filename", filename)
    newFilename = filename + ".JSON"
    meta.writeJSON(newFilename)

def main():
    """Main function that converts a test file"""
    paths = []
    #paths.append("../Data/Test")
    paths.append("../Data/Test/Maps")
    paths.append("../Data/R6GOG")
    paths.append("../Data/RSDemo")

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths = fp.paths + paths
    fp.fileExt = ".MAP"

    fp.processFunction = convert_MAP

    #fp.run_sequential()
    fp.run_async()

if __name__ == "__main__":
    main()
