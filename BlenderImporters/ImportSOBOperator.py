import sys

import bpy
# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

# TODO: find a better way to load this module from Blender.
sys.path.insert(0, 'E:/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/Users/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
sys.path.insert(0, '/home/philipedwards/Dropbox/Development/Rainbow/RainbowSixFileConverters')
from BlenderImporters import ImportSOB

def import_SOB(context, filename, use_some_setting):
    print("running read_some_data...")
    ImportSOB.import_SOB_to_scene(filename)
    return {'FINISHED'}

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
        return import_SOB(context, self.filepath, self.use_setting)


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
