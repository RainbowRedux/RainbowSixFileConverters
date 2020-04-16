"""
Converts RSB files to png files and an acompanying JSON file with extra meta data
information for file format from here:
https://github.com/AlexKimov/RSE-file-formats/wiki/RSB-File-Format
https://github.com/AlexKimov/RSE-file-formats/blob/master/010Editor-templates/RSB.bt
RSB Version 0 required looking into the bt file directly as the wiki is not complete
Texture and surface data extraction to JSON file is not complete
"""

import logging

from RainbowFileReaders.SOBModelReader import SOBModelFile
from RainbowFileReaders.MathHelpers import Vector
from FileUtilities.Settings import load_settings
from FileUtilities import DirectoryProcessor
from FileUtilities import JSONMetaInfo, OBJModelWriter

log = logging.getLogger(__name__)

#TODO: Improve logging for async. Add write out to file handler, which outputs txt for each file, and configure logging in each thread.
logging.basicConfig(level=logging.INFO)

def convert_SOB(filename):
    """ Reads an SOB file and then writes to OBJ format """
    log.info("Processing: %s", filename)

    modelFile = SOBModelFile()
    modelFile.read_file(filename)

    meta = JSONMetaInfo.JSONMetaInfo()
    meta.add_info("filecontents", modelFile)
    meta.add_info("filename", filename)
    newFilename = filename + ".JSON"
    meta.writeJSON(newFilename)

    countBadNormals = 0
    countGoodNormals = 0
    for geoObj in modelFile.geometryObjects:
        for vertexParam in geoObj.vertexParams:
            if Vector.is_normal(vertexParam.normal):
                countGoodNormals += 1
            else:
                countBadNormals += 1

    if countBadNormals > 0:
        log.warning("Num bad normals: %d", countBadNormals)
    else:
        log.info("Num bad normals: %d", countBadNormals)
    log.info("Num good normals: %d", countGoodNormals)

    write_OBJ(filename + ".obj", modelFile)

    log.info("===============================================")

def write_OBJ(filename, SOBObject: SOBModelFile):
    """Writes the given Geometry Object to an OBJ file """
    writer = OBJModelWriter.OBJModelWriter()
    writer.open_file(filename)
    for geoObject in SOBObject.geometryObjects:
        writer.begin_new_object(geoObject.name_string.string)
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
    """Main function that converts test data files"""
    settings = load_settings()

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths.append(settings["gamePath"])
    fp.fileExt = ".SOB"

    fp.processFunction = convert_SOB

    fp.run(mode=settings["runMode"])

if __name__ == "__main__":
    main()
