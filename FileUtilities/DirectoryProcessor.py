import random
import multiprocessing
import os
from os.path import join

def processorNotImplementedDefault(path):
    print("No processor has been assigned, so no processing will be performed on: " + str(path))

def gather_files_in_path(extension, folder):
    filesToProcess = []
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            if name.upper().endswith(extension):
                filesToProcess.append(join(root, name))
        for name in dirs:
            print("Walking directory: " + os.path.join(root, name))
    return filesToProcess

class DirectoryProcessor(object):
    paths = []
    fileExt = ".none"
    processFunction = processorNotImplementedDefault
    allFiles = []

    def gather_all_files(self):
        files = []
        for path in self.paths:
            newFiles = gather_files_in_path(self.fileExt, path)
            files = files + newFiles
        self.allFiles = files

    def run_async(self):
        self.gather_all_files()

        # Large files tend to be grouped in folders, which can lead to many large files being assigned to one worker
        # A shuffle helps more evenly distribute processing workload
        random.shuffle(self.allFiles)

        numWorkers = multiprocessing.cpu_count()

        print("Number of files found to process: " + str(len(self.allFiles)))
        print("Number of workers: " + str(numWorkers))

        pool = multiprocessing.Pool(numWorkers)
        pool.map(self.processFunction, self.allFiles)


    def run_sequential(self):
        self.gather_all_files()
        for path in self.allFiles:
            # Pylint disabled error E1121 as it is a false positive
            self.processFunction(path) # pylint: disable=E1121

    def profileRun(self):
        self.run_sequential()

    # pylint Disabled R0201 since i want this to be an option for developers to run easily for instances of this class, allowing easy profiling of their code
    def profile(self):  # pylint: disable=R0201
        import cProfile
        #TODO: check this is valid
        cProfile.run('self.profileRun')
