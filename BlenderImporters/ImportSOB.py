import random
import os
import sys

import bpy
import bmesh

sys.path.insert(0, 'C:/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders import R6Settings

def sanitize_float(inFloat):
    return "{0:.8f}".format(inFloat)
    return str(inFloat)

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
        faces = []

        print("Number of faces to import: " + str(geoObj.faceCount))
        print("Number of verts to import: " + str(geoObj.vertexCount))
        for face in geoObj.faces:
            faces.append(face.vertexIndices)
        #use this over bmesh, as it will allow faces that share vertices with different windings
        newMesh.from_pydata(geoObj.vertices, [], faces)

        # Update mesh with new data
        newMesh.update(calc_edges=True)

        ########################################
        # Copy to bmesh
        ########################################

        newBmesh = bmesh.new()
        newBmesh.from_mesh(newMesh)
        color_layer = newBmesh.loops.layers.color.new("color")
        uv_layer = newBmesh.loops.layers.uv.verify()
        newBmesh.faces.layers.tex.verify()  # currently blender needs both layers.

        print("Number of faces: " + str(len(newBmesh.faces)))

        ########################################
        # Apply Vertex Colors
        ########################################

        # Cobbled together from : https://blender.stackexchange.com/a/60730
        #newBmesh = bmesh.new()   # create an empty BMesh
        #newBmesh.from_mesh(newMesh)
        #color_layer = newBmesh.loops.layers.color.new("color")

        print("Number of vertices: " + str(len(newBmesh.verts)))

        max_loop = 0
        for face_index, face in enumerate(newBmesh.faces):
            if face is None:
                continue
            importedParamIndices = geoObj.faces[face_index].paramIndices
            for vert_index, vert in enumerate(face.loops):
                if vert_index > max_loop:
                    max_loop = vert_index
                importedColor = geoObj.vertexParams[importedParamIndices[vert_index]].color
                for i in range(len(importedColor)):
                    importedColor[i] = importedColor[i] / 255.0
                vert[color_layer] = importedColor

        print("Max loop index: " + str(max_loop))
        #newBmesh.to_mesh(newMesh)

        ########################################
        # Apply UV Mapping
        ########################################
        # Cobbled together from https://docs.blender.org/api/blender_python_api_2_67_release/bmesh.html#customdata-access
        # Create Bmesh
        #newBmesh = bmesh.new()   # create an empty BMesh
        #newBmesh.from_mesh(newMesh)
        #uv_layer = newBmesh.loops.layers.uv.verify()
        #newBmesh.faces.layers.tex.verify()  # currently blender needs both layers.

        uniqueVerts = []

        for face_index, face in enumerate(newBmesh.faces):
        #for face_index, face in enumerate(createdFaces):
            if face is None:
                continue
            importedParamIndices = geoObj.faces[face_index].paramIndices
            for vert_index, vert in enumerate(face.loops):
                if vert not in uniqueVerts:
                    uniqueVerts.append(vert)
                importedUV = geoObj.vertexParams[importedParamIndices[vert_index]].UV
                if importedUV[0] > 1.0 or importedUV[0] < -1.0:
                    pass
                    #print("x uv coord fucked: " + sanitize_float(importedUV[0]))
                if importedUV[1] > 1.0 or importedUV[1] < -1.0:
                    pass
                    #print("y uv coord fucked: " + sanitize_float(importedUV[1]))
                vert[uv_layer].uv.x = importedUV[0]
                vert[uv_layer].uv.y = importedUV[1]
        newBmesh.to_mesh(newMesh)
        newMesh.update(calc_edges=True)

        print("Number of vertex uv params: " + str(len(uniqueVerts)))

        ########################################
        # Apply Materials per face
        ########################################
        for i in range(len(newMesh.polygons)):
            poly = newMesh.polygons[i]
            faceProperties = geoObj.faces[i]
            if faceProperties.materialIndex != R6Settings.UINT_MAX:
                poly.material_index = faceProperties.materialIndex

        #newBmesh.to_mesh(newMesh)


        # TODO: Import normals

    print("Success")

def fixup_texture_name(filename):
    ext = filename.lower()[-4:]
    newfilename = filename
    if ext == ".bmp" or ext == ".rsb" or ext == ".tga":
        newfilename = newfilename[:-4]
        newfilename += ".PNG"
    return newfilename


def find_texture(filename, dataPath):
    if filename.lower() == "null":
        return None
    newfilename = fixup_texture_name(filename)
    result = None
    for root, dirs, files in os.walk(dataPath):
        for name in files:
            # Compare lowercase versions since windows is case-insensitive
            if name.lower().endswith(newfilename.lower()):
                result = os.path.join(root, name)
                #print("Found " + result)
        for name in dirs:
            pass
    if result is None:
        print("Failed to find texture: " + newfilename)
    return result


def create_material_from_SOB_specification(materialSpecification, gameDataPath):
    # set new material to variable
    newMaterial = bpy.data.materials.new(name=materialSpecification.materialName)
    
    texturePath = os.path.join(gameDataPath, R6Settings.paths["TexturePath"])
    texturePath = os.path.normpath(texturePath)

    texToLoad = materialSpecification.textureName
    texToLoad = find_texture(texToLoad, texturePath)
    print("Final texture to load: " + str(texToLoad))

    if texToLoad is not None:
        # Texture loading code adapted from https://stackoverflow.com/q/19076062
        # Load the image
        texImage = bpy.data.images.load(texToLoad)
        # Create texture from image
        newTexture = bpy.data.textures.new('ColorTex', type = 'IMAGE')
        newTexture.image = texImage
        # TODO: Revisit opacity specification for diffuse mat?
        newTexture.use_alpha = materialSpecification.opacity < 1.0

        # Add texture slot for color texture
        textureSlot = newMaterial.texture_slots.add()
        textureSlot.texture = newTexture

        textureSlot.use_map_color_diffuse = True 
        textureSlot.texture_coords = 'UV'

    newMaterial.use_shadeless = True
    

    # Generate random material diffuse colour for now, to aid debugging.
    #r = random.uniform(0, 1)
    #g = random.uniform(0, 1)
    #b = random.uniform(0, 1)
    #newMaterial.diffuse_color = (r, g, b)  # change color
    return newMaterial

if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene(sys.argv[-1])