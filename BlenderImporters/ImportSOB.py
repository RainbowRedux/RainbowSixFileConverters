import random
import os
import sys

import bpy

sys.path.insert(0, 'C:/Users/philipedwards/Dropbox/Development/RainbowSixFileConverters')
from RainbowFileReaders import SOBModelReader

def import_SOB_to_scene(filename):
    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_sob(filename)
    filepath = os.path.dirname(filename)
    
    print("")
    print("Beginning import")

    print("File is in directory: " + filepath)
    gameDataPath = os.path.split(filepath)[0]
    print("Assuming gamepath is: " + gameDataPath)

    for geoObj in SOBObject.geometryObjects:
        name = geoObj.objectName

        ########################################
        # Create blender objects
        ########################################

        newMesh = bpy.data.meshes.new(name +'Mesh')
        newObject = bpy.data.objects.new(name, newMesh)
        newObject.location = (0,0,0)
        newObject.show_name = True
        # Link object to scene
        bpy.context.scene.objects.link(newObject)

        ########################################
        # Import materials
        ########################################
        # TODO: Revisit material definitions. Currently will create a material for each mesh, which is likely not the desired effect
        blenderMaterials = []

        for materialSpec in SOBObject.materials:
            newMaterial = create_material_from_SOB_specification(materialSpec, gameDataPath)
            newObject.data.materials.append(newMaterial)
            blenderMaterials.append(newMaterial)
        
        # TODO: Import textures

        ########################################
        # Define vertices & faces
        ########################################

        # Create mesh from given verts, edges, faces. Either edges or
        # faces should be [], or you ask for problems
        faces = []
        for face in geoObj.faces:
            faces.append(face.vertexIndices)
        newMesh.from_pydata(geoObj.vertices, [], faces)

        # Update mesh with new data
        newMesh.update(calc_edges=True)

        ########################################
        # Apply Vertex Colors
        ########################################

        # for safety from here: https://blender.stackexchange.com/a/8561
        # probably not needed
        if newMesh.vertex_colors:
            newVertexColors = newMesh.vertex_colors.active
        else:
            newVertexColors = newMesh.vertex_colors.new()

        for i in range(len(newMesh.polygons)):
            poly = newMesh.polygons[i]
            paramIndices = geoObj.faces[i].paramIndices
            for loop_index in poly.loop_indices:
                color = geoObj.vertexParams[paramIndices[loop_index % 3]].color
                for i in range(len(color)):
                    color[i] = color[i] / 255.0
                newVertexColors.data[loop_index].color = color

        ########################################
        # Apply Materials per face
        ########################################
        for i in range(len(newMesh.polygons)):
            poly = newMesh.polygons[i]
            faceProperties = geoObj.faces[i]
            if faceProperties.materialIndex != 4294967295:
                poly.material_index = faceProperties.materialIndex

        # TODO: Import normals

    print("Success")

def find_texture(filename, gameDataPath):
    pass


def create_material_from_SOB_specification(materialSpecification, gameDataPath):
    # set new material to variable
    newMaterial = bpy.data.materials.new(name=materialSpecification.materialName)
    # Generate random material diffuse colour for now, to aid debugging.
    r = random.uniform(0, 1)
    g = random.uniform(0, 1)
    b = random.uniform(0, 1)
    newMaterial.diffuse_color = (r, g, b)  # change color
    return newMaterial

if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene("C:\\Users\\philipedwards\\Dropbox\\Development\\RainbowSixFileConverters\\Data\\R6\\data\\model\\cessna.sob")