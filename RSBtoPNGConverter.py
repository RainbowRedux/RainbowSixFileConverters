"""
Converts RSB files to png files and an acompanying JSON file with extra meta data
 information for file format from here:
 https://github.com/AlexKimov/RSE-file-formats/wiki/RSB-File-Format
 https://github.com/AlexKimov/RSE-file-formats/blob/master/010Editor-templates/RSB.bt
 RSB Version 0 required looking into the bt file directly as the wiki is not complete
 Texture and surface data extraction to JSON file is not complete

 On an i7-7700 conversion of the entire GOG copy of rainbow six takes around 4 minutes.
 This process could be heavily optimised if array slicing is minimised and more care is
 taken around memory copies, but since it's a once off process, I'm not too concerned with speed

Files with DXT compressed images don't recover the image, since i haven't worked on decompressing DXT images
Files with a format version later than 1 also store information after the image, currently this is discarded but can easily be added.
"""

import os

from RainbowFileReaders.RSBImageReader import RSBImageFile
from FileUtilities import JSONMetaInfo, DirectoryProcessor

def convert_RSB(filename):
    """Reads an RSB file and writes to 2 PNGs (or 1 if there is not palette version stored) """
    print("Processing: " + filename)

    imageFile = RSBImageFile()
    imageFile.read_file(filename)

    #create and save png from 256 color image
    if imageFile.image256 is not None:
        newImg1 = imageFile.convert_palette_image()
        newFilename = filename + ".256.PNG"
        newImg1.save(newFilename, "PNG")

    #create and save png from full color image
    newImg2 = imageFile.convert_full_color_image()
    newFilename = filename + ".PNG"
    newImg2.save(newFilename, "PNG")

    #save meta data to JSON file
    newFilename = newFilename.replace(".PNG", ".JSON")
    meta = JSONMetaInfo.JSONMetaInfo()
    meta.setFilename(os.path.basename(filename))
    meta.add_info("header", imageFile.header)
    meta.writeJSON(newFilename)

    print("Finished converting: " + filename)
    print("")

def main():
    """Main function that converts test data files"""
    import ProcessorPathsHelper
    paths = ProcessorPathsHelper.get_paths()
    for path in paths:
        print(path)

    fp = DirectoryProcessor.DirectoryProcessor()
    fp.paths = fp.paths + paths
    fp.fileExt = ".RSB"

    fp.processFunction = convert_RSB

    #fp.run_sequential()
    fp.run_async()

if __name__ == "__main__":
    main()
    #profile()
