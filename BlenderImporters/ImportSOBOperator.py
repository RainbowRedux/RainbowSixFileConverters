import bpy
import random
import sys
# TODO: find a better way to load this module from Blender.
sys.path.insert(0, 'C:/Users/philipedwards/Dropbox/Development/RainbowSixFileConverters')

import RainbowFileReaders
from RainbowFileReaders import SOBModelReader

def ImportSOB(context, filepath, use_some_setting):
    print("running read_some_data...")

    SOBObject = SOBModelReader.SOBModelFile()
    SOBObject.read_sob(filepath)

    # would normally load the data here
    SOBObject.header.print_header_info()

    for geoObj in SOBObject.geometryObjects:
        name = geoObj.objectName

        ########################################
        # Create blender objects
        ########################################

        newMesh = bpy.data.meshes.new(name +'Mesh')
        newObject = bpy.data.objects.new(name, newMesh)
        print(str(newObject.location))
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
            newMaterial = CreateMaterial(materialSpec)
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
        print(len(faces))
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

    return {'FINISHED'}

def CreateMaterial(materialSpecification):
    # set new material to variable
    newMaterial = bpy.data.materials.new(name=materialSpecification.materialName)
    r = random.uniform(0, 1)
    g = random.uniform(0, 1)
    b = random.uniform(0, 1)
    newMaterial.diffuse_color = (r, g, b)  # change color
    return newMaterial


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportR6SOB(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_rs.sob"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import R6 SOB"

    # ImportHelper mixin class uses this
    filename_ext = ".SOB"

    filter_glob = StringProperty(
            default="*.sob",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting = BoolProperty(
            name="Example Boolean",
            description="Example Tooltip",
            default=True,
            )

    type = EnumProperty(
            name="Example Enum",
            description="Choose between two items",
            items=(('OPT_A', "First Option", "Description one"),
                   ('OPT_B', "Second Option", "Description two")),
            default='OPT_A',
            )

    def execute(self, context):
        return ImportSOB(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportR6SOB.bl_idname, text="Text Import Operator")


def register():
    bpy.utils.register_class(ImportR6SOB)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportR6SOB)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_rs.sob('INVOKE_DEFAULT')
