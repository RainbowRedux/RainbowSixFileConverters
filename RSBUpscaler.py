from TextureUpscaler.TextureProcessing import *
from TextureUpscaler.UpscaleESRGAN import *

SourcePath = "D:\\R6Data\\FullGames\\R6EWCD\\"
WorkingPath = "D:\\R6Data\\workingdir\\"
ExtensionsToFind = [".CACHE.PNG"]

if __name__ == "__main__":
    images = gather_textures(SourcePath, WorkingPath, ExtensionsToFind)
    print(len(images))
    run_processing_stage(denoise_texture, images)
    upscale_esrgan(images, WorkingPath)
    run_processing_stage(save_hires_image, images)
