import random
import os
import sys

import bpy
import bmesh

sys.path.insert(0, 'C:/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from RainbowFileReaders import SOBModelReader
from RainbowFileReaders.SOBModelReader import SOBAlphaMethod
from RainbowFileReaders import R6Settings
from RainbowFileReaders.R6Constants import UINT_MAX
from RainbowFileReaders.MathHelpers import normalize_color, sanitize_float

def import_SOB_to_scene(filename):
    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_sob(filename)
    filepath = os.path.dirname(filename)
    
    print("")
    print("Beginning import")

    print("File is in directory: " + filepath)
    gameDataPath = os.path.split(filepath)[0]
    print("Assuming gamepath is: " + gameDataPath)

    #TODO Add step for converting from LHS to RHS, and probably rotating to having another axis as the up axis

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
        # Copy to bmesh from mesh
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
        for face_index, face in enumerate(newBmesh.faces):
            if face is None:
                continue
            importedParamIndices = geoObj.faces[face_index].paramIndices
            for vert_index, vert in enumerate(face.loops):
                importedColor = geoObj.vertexParams[importedParamIndices[vert_index]].color
                importedColor = normalize_color(importedColor)
                vert[color_layer] = importedColor

        ########################################
        # Apply UV Mapping
        ########################################
        # Cobbled together from https://docs.blender.org/api/blender_python_api_2_67_release/bmesh.html#customdata-access
        for face_index, face in enumerate(newBmesh.faces):
            if face is None:
                continue
            importedParamIndices = geoObj.faces[face_index].paramIndices
            for vert_index, vert in enumerate(face.loops):
                importedUV = geoObj.vertexParams[importedParamIndices[vert_index]].UV
                vert[uv_layer].uv.x = importedUV[0]
                # This coord seems to be inverted, this seems to look correct.
                vert[uv_layer].uv.y = importedUV[1] * -1
        
        ########################################
        # Copy from bmesh back to mesh
        ########################################
        
        newBmesh.to_mesh(newMesh)
        newMesh.update(calc_edges=True)

        ########################################
        # Apply Materials per face
        ########################################
        for i in range(len(newMesh.polygons)):
            poly = newMesh.polygons[i]
            faceProperties = geoObj.faces[i]
            #Do not assign a material if index is UINT_MAX
            if faceProperties.materialIndex != R6Settings.UINT_MAX:
                poly.material_index = faceProperties.materialIndex


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
    """Creates a material from an SOB specification.
    This does ignore some values that don't map well to PBR and don't influence model behaviour much.
    Materials will be more finely tuned in the game engine.
    
    materialSpecification is an RSEMaterialDefinition as read by SOBModelReader

    gameDataPath is meant to be the Data folder within the games installation
        directory, as that directory structure is used when loading textures"""

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

        # Add texture slot for color texture
        textureSlot = newMaterial.texture_slots.add()
        textureSlot.texture = newTexture

        textureSlot.use_map_color_diffuse = True
        textureSlot.texture_coords = 'UV'

        if materialSpecification.alphaMethod != SOBAlphaMethod.SAM_Solid:
            newTexture.use_alpha = True
            textureSlot.use_map_alpha = True
            textureSlot.alpha_factor = materialSpecification.opacity

    if materialSpecification.alphaMethod != SOBAlphaMethod.SAM_Solid:
        print(materialSpecification.materialName)
        print(str(materialSpecification.alphaMethod))
        print(str(SOBAlphaMethod.SAM_Solid))
        newMaterial.use_transparency = True
        #Blenders material transparency method is different to how masked alpha would work in a game engine,
        # this still provides alpha blending, but if you use Z method the transparent part of the surface
        # still has specular properties. In this instance, MASK provides expected results
        newMaterial.transparency_method = 'MASK'

        if texToLoad is not None:
            newMaterial.alpha = 0.0
        else:
            #TODO: Check that opacity is not used when alphaMethod == 1 or SAM_Solid
            newMaterial.alpha = materialSpecification.opacity

    # TODO: work out if materialSpecification.ambient should be averaged and applied
    # to newMaterial.ambient, or if it's for the lighting model that might be
    # specified in materialSpecification.unknown2
    newMaterial.diffuse_color = normalize_color(materialSpecification.diffuse)  # change color
    newMaterial.specular_color = normalize_color(materialSpecification.specular)
    newMaterial.specular_intensity = materialSpecification.specularLevel


    return newMaterial

if __name__ == "__main__":
    #this is used when running this python file as a headless task
    import_SOB_to_scene(sys.argv[-1])