import platform

def get_data_path():
    if platform.system() == "Linux":
        raise NotImplementedError
    if platform.system() == "Darwin":
        return "~/Desktop/R6Data"
    if platform.system() == "Windows":
        return "D:/R6Data"
    raise NotImplementedError

def expand_paths(inPaths):
    PathPrefix = get_data_path()

    newPaths = []
    import os
    for path in inPaths:
        newPaths.append(os.path.join(PathPrefix, path))

    return newPaths

def get_paths():
    paths = []
    paths.append("TestData")
    #paths.append("FullGames")
    #paths.append("")

    return expand_paths(paths)


if __name__ == "__main__":
    import pprint
    pprint.pprint(get_paths())
