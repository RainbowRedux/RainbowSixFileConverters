#Converts RSB files to png files and an acompanying JSON file with extra meta data
#information for file format from here:
#https://github.com/AlexKimov/RSE-file-formats/wiki/RSB-File-Format
#https://github.com/AlexKimov/RSE-file-formats/blob/master/010Editor-templates/RSB.bt
#RSB Version 0 required looking into the bt file directly as the wiki is not complete
#Texture and surface data extraction to JSON file is not complete

from PIL import Image
import time
import os
import DirectoryProcessor
import json

from RainbowFileReaders import SOBModelReader
from FileWriters import JSONMetaInfo, OBJModelWriter
from RainbowFileReaders.MathHelpers import is_vector_normal

def convert_SOB(filename):
    print("Processing: " + filename)

    modelFile = SOBModelReader.SOBModelFile()
    modelFile.read_sob(filename, verboseOutput=False)

    meta = JSONMetaInfo.JSONMetaInfo()
    meta.add_info("filecontents", modelFile)
    meta.add_info("filename", filename)
    newFilename = filename + ".JSON"
    meta.writeJSON(newFilename)

    countBadNormals = 0
    countGoodNormals = 0
    for geoObj in modelFile.geometryObjects:
        for vertexParam in geoObj.vertexParams:
            if is_vector_normal(vertexParam.normal):
                countGoodNormals += 1
            else:
                countBadNormals += 1
            
    print("Num bad normals: " + str(countBadNormals))
    print("Num good normals: " + str(countGoodNormals))

    write_OBJ(filename + ".obj", modelFile)

    print("===============================================")

def write_OBJ(filename, SOBObject):
    writer = OBJModelWriter.OBJModelWriter()
    writer.open_file(filename)
    for geoObject in SOBObject.geometryObjects:
        writer.begin_new_object(geoObject.objectName)
        #write vertices
        for i in range(len(geoObject.vertices)):
            vertex = geoObject.vertices[i]
            writer.write_vertex(vertex)
        #write vertex parameters
        for i in range(len(geoObject.vertexParams)):
            normal = geoObject.vertexParams[i].normal
            writer.write_normal(normal)
            UV = geoObject.vertexParams[i].UV
            writer.write_texture_coordinate(UV)
        #write face definitions
        for face in geoObject.faces:
            writer.write_face(face.vertexIndices,face.paramIndices, face.paramIndices)
    writer.close_file()

def main():
    """Main function that converts a test file"""
    """Main function that converts test data files"""
    paths = []
    paths.append("../Data/Test")
    paths.append("../Data/R6GOG")
    paths.append("../Data/RSDemo")

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths = fp.paths + paths
    fp.fileExt = ".SOB"

    fp.processFunction = convert_SOB

    #fp.run_sequential()
    fp.run_async()

if __name__ == "__main__":
    main()
