class OBJModelWriter(object):
    def __init__(self):
        pass
        self.output_file = None

    def open_file(self, path):
        self.close_file()
        if path is not None and len(path) != 0:
            self.output_file = open(path, "w")
        if self.output_file is None:
            print("Could not open file for output: " + str(path))
            return

    def close_file(self):
        if self.output_file is not None:
            self.output_file.close()
            self.output_file = None

    def write_line(self, newline):
        if self.output_file is not None:
            self.output_file.write(newline)
            self.output_file.write("\n")

    def begin_new_object(self, ObjectName = "Undefined"):
        newline = "o "
        newline += str(ObjectName)
        self.write_line(newline)

    AxisOrdering = [0, 2, 1, 3]
    AxisOrdering = [2, 0, 1, 3]

    def sanitize_float(self, inFloat):
        return "{0:.8f}".format(inFloat)

    def write_vertex(self, vertex):
        newline = "v "
        for index in range(len(vertex)):
            newline += self.sanitize_float(vertex[self.AxisOrdering[index]])
            newline += " "
        newline.strip()
        self.write_line(newline)

    def write_normal(self, normal):
        newline = "vn "
        for index in range(len(normal)):
            newline += self.sanitize_float(normal[self.AxisOrdering[index]])
            newline += " "
        newline.strip()
        self.write_line(newline)

    def write_texture_coordinate(self, UV):
        newline = "vt "
        newline += self.sanitize_float(UV[0])
        newline += " "
        newline += self.sanitize_float(UV[1])
        self.write_line(newline)

    def write_face(self, vertex_indices, texture_coord_indices, normal_indices):
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

        self.write_line(newline)
