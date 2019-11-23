"""
Utilities to run various processing and upscaling processes on images
"""

from os import path
from shutil import copyfile

from FileUtilities.DirectoryUtils import gather_files_in_path

class WorkingImageData:
    """Information associated with an image that is running through the processing pipeline"""
    originalPath = ""
    ID = 0
    workingPath = ""
    workingFilename = ""
    filename = ""
    lastPath = ""

    def assign_file(self, filepath, ID, workingPath):
        self.originalPath = path.normpath(filepath)
        self.ID = ID
        self.filename = path.basename(self.originalPath)
        self.workingFilename = str(self.ID) + ".PNG"
        self.workingPath = path.join(workingPath, self.workingFilename)
        self.lastPath = self.originalPath

#Gather Textures
    #Find all .PNG
    #put into list of objects
    #assign ID
def gather_textures(source_path, workingPath, extensionsToFind):
    """
    Finds all textures and returns them in the workingImage data structure
    """
    filepaths = []
    for ext in extensionsToFind:
        filepaths.extend(gather_files_in_path(ext, source_path))

    print(len(filepaths))

    workingImages = []
    lastID = 0
    for filepath in filepaths:
        procImage = WorkingImageData()
        procImage.assign_file(filepath, lastID, workingPath)
        lastID += 1
        workingImages.append(procImage)

    return workingImages

def run_processing_stage(processingFunc, workingImages):
    """Runs the function passed to processingFunc on each working image."""
    for workingImage in workingImages:
        print("Processing: " + str(workingImage.ID))
        result = processingFunc(workingImage.lastPath, workingImage.workingPath, workingImage)
        if result:
            workingImage.lastPath = workingImage.workingPath

def invert_texture(inpath, outpath, workingImage):
    """Inverts the colors on the texture specified"""
    print("Inverting texture: " + inpath)
    from PIL import Image
    import PIL.ImageOps
    image = Image.open(inpath)
    inverted_image = None
    try:
        inverted_image = PIL.ImageOps.invert(image)
    except:
        return False
    inverted_image.save(outpath)
    return True

def denoise_texture(inpath, outpath, workingImage):
    """Runs a denoising process on the texture specified"""
    import cv2 as cv
    img = cv.imread(inpath)
    dst = cv.fastNlMeansDenoisingColored(src=img,dst=None,h=5,hColor=5,templateWindowSize=1,searchWindowSize=5)
    cv.imwrite(outpath,dst)

def save_hires_image(inpath, outpath, workingImage):
    """Takes a working image and saves it in the original place with .HIRES before the original extension"""
    src = inpath
    ext = path.splitext(workingImage.originalPath)[1]
    dst = workingImage.originalPath[:-len(ext)] + ".HIRES" + ext
    print("source: " + src)
    print("\tdest: " + dst)
    copyfile(src, dst)

#Upscale Textures
    #ESRGAN
        #Choose Model (PSNR or RRGAN)
        #Copy Preprocessed images to LR folder
        #Run Process
    #GigaPixel
        #???
    #Topaz
        #???

#PostProcess Textures
    #Correct Alpha Channels
        #Resize Textures with Pillow
        #Copy Alpha Channel Across
    
    #Remove edge highlights (optional)

    #Merge results (optional)
        #Blend outputs of multiple upscaled textures
    
    #resize to reduce artifacts (optional)

#Output Images
    #Save all images next to original images with the extension of .HIRES.PNG