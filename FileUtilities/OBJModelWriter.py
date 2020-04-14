"""
Provides a class that can writes valid OBJ model files
"""
import logging

from RainbowFileReaders.MathHelpers import sanitize_float

log = logging.getLogger(__name__)

class OBJModelWriter(object):
    """Class to write OBJ file"""
    def __init__(self):
        self.output_file = None

    def open_file(self, path):
        """Opens a file for writing at specified path"""
        self.close_file()
        if path:
            self.output_file = open(path, "w")
        if self.output_file is None:
            log.error("Could not open file for output: %s", path)
            return

    def close_file(self):
        """Closes the open file and finalises file"""
        if self.output_file is not None:
            self.output_file.close()
            self.output_file = None

    def _writeline(self, newline: str):
        """Writes a text line to the file"""
        if self.output_file is not None:
            self.output_file.write(newline)
            self.output_file.write("\n")

    def begin_new_object(self, ObjectName: str="Undefined"):
        """Writes a begin object statement to file"""
        newline = "o "
        newline += str(ObjectName)
        self._writeline(newline)

    AxisOrdering = [0, 2, 1, 3]
    AxisOrdering = [2, 0, 1, 3]

    def write_vertex(self, vertex):
        """Writes a vertex to the file. Vertex is list of 3 floats"""
        newline = "v "
        for index in range(len(vertex)):
            newline += sanitize_float(vertex[self.AxisOrdering[index]])
            newline += " "
        newline.strip()
        self._writeline(newline)

    def write_normal(self, normal):
        """Writes a normal to the file. normal is list of 3 floats"""
        newline = "vn "
        for index in range(len(normal)):
            newline += sanitize_float(normal[self.AxisOrdering[index]])
            newline += " "
        newline.strip()
        self._writeline(newline)

    def write_texture_coordinate(self, UV):
        """Writes a UV to the file. UV is list of 2 floats"""
        newline = "vt "
        newline += sanitize_float(UV[0])
        newline += " "
        newline += sanitize_float(UV[1])
        self._writeline(newline)

    def write_face(self, vertex_indices, texture_coord_indices, normal_indices):
        """Writes a face to the file. Indices are 1 based, not 0 based.
        All referenced vertices, texture coords and normals should be written before this is written"""
        newline = "f "
        #Vertex index ordering should match the cardinal axis ordering specified in write_vertex
        #if this is not matched then face winding will be incorrect
        for index in range(3):
            newline += str(vertex_indices[self.AxisOrdering[index]] + 1)
            newline += "/"
            newline += str(texture_coord_indices[self.AxisOrdering[index]] + 1)
            newline += "/"
            newline += str(normal_indices[self.AxisOrdering[index]] + 1)

            newline += " "

        self._writeline(newline)
