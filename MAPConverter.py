""" A commandline utilty to read map files and output their data into JSON files """
from RainbowFileReaders import MAPLevelReader
from RainbowFileReaders.R6Constants import RSEGameVersions
from FileUtilities import JSONMetaInfo, DirectoryProcessor

lightTypes = []


def strip_extra_data_for_json(mapFile):
    """ Strips out lengthy data which is already being interpreted correctly to make it easier for humans to view the json file """
    for geometryObject in mapFile.geometryObjects:
        if mapFile.gameVersion == RSEGameVersions.RAINBOW_SIX:
            geometryObject.vertices = ["Stripped from JSON"]
            geometryObject.vertexParams = ["Stripped from JSON"]
            geometryObject.faces = ["Stripped from JSON"]
            for mesh in geometryObject.meshes:
                mesh.faceIndices = ["Stripped from JSON"]
        else:
            geometryObject.geometryData.vertices = ["Stripped from JSON"]
            for facegroup in geometryObject.geometryData.faceGroups:
                facegroup.faceVertexIndices = ["Stripped from JSON"]
                facegroup.faceVertexParamIndices = ["Stripped from JSON"]
                facegroup.vertexParams = ["Stripped from JSON"]
                facegroup.faceNormals = ["Stripped from JSON"]
                facegroup.faceDistancesFromOrigin = ["Stripped from JSON"]

            geometryObject.geometryData.collisionInformation.vertices = ["Stripped from JSON"]
            geometryObject.geometryData.collisionInformation.normals = ["Stripped from JSON"]
            geometryObject.geometryData.collisionInformation.faceDistancesFromOrigin = ["Stripped from JSON"]
            geometryObject.geometryData.collisionInformation.faces = ["Stripped from JSON"]
            geometryObject.geometryData.collisionInformation.collisionMeshDefinitions = ["Stripped from JSON"]

flagErrors = []

def convert_MAP(filename):
    """ Reads in MAP files, and then converts to JSON """
    print("Processing: " + filename)
    if filename.endswith("obstacletest.map"):
        #I believe this is an early test map that was shipped by accident.
        # It's data structures are not consistent with the rest of the map files
        # and it is not used anywhere so it is safe to skip
        print("Skipping test map: " + filename)
        return

    mapFile = MAPLevelReader.MAPLevelFile()
    mapFile.read_file(filename, True)

    for geometryObject in mapFile.geometryObjects:
        if mapFile.gameVersion == RSEGameVersions.RAINBOW_SIX:
            for mesh in geometryObject.meshes:
                if mesh.geometryFlagsEvaluated["UnevaluatedFlags"]:
                    errorMessage = filename + " UnevaluatedFlags for:" + geometryObject.nameString + "_" + mesh.nameString
                    flagErrors.append(errorMessage)
                    print(errorMessage)
                geometryObject.generate_renderable_arrays_for_mesh(mesh)
        elif mapFile.gameVersion == RSEGameVersions.ROGUE_SPEAR:
            #Rogue Spear
            for collisionMeshDefinition in geometryObject.geometryData.collisionInformation.collisionMeshDefinitions:
                if collisionMeshDefinition.geometryFlagsEvaluated["UnevaluatedFlags"]:
                    errorMessage = filename + " UnevaluatedFlags for:" + geometryObject.nameString + "_" + mesh.nameString
                    flagErrors.append(errorMessage)
                    print(errorMessage)
        else:
            print("Unable to determine where geometryFlags are")


    for light in mapFile.lightList.lights:
        if light.type not in lightTypes:
            lightTypes.append(light.type)

    strip_extra_data_for_json(mapFile)

    meta = JSONMetaInfo.JSONMetaInfo()
    meta.add_info("filecontents", mapFile)
    meta.add_info("filename", filename)
    newFilename = filename + ".JSON"
    meta.writeJSON(newFilename)

def main():
    """Main function that converts a test file"""
    import ProcessorPathsHelper
    paths = ProcessorPathsHelper.get_paths()

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths = fp.paths + paths
    fp.fileExt = ".MAP"

    fp.processFunction = convert_MAP

    fp.run_sequential()
    #fp.run_async()

    print("Light Types: ")
    print(lightTypes)
    print("Geometry Flag errors: ")
    for err in flagErrors:
        print(err)

if __name__ == "__main__":
    main()
