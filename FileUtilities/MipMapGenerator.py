"""Utilities to help working with images"""

import PIL

def is_power_of_2(number):
    """Checks if a number is a power of 2"""
    num1 = ((number & (number - 1)) == 0)
    return num1

def halve_image_dimensions(dimensions):
    """
    Halves image dimensions. Returns ints. No new dimension will be less than 1"""
    new_dimensions = [x/2 for x in dimensions]
    new_dimensions = [int(x) for x in new_dimensions]
    new_dimensions = [max(x, 1) for x in new_dimensions]
    return tuple(new_dimensions)


def generate_mip_maps(src_image):
    """
    Generate a list of images suitable for use as MipMaps
    src_image should be a PIL.Image with Power Of 2 dimensions
    Returns list of images, 0th element being the src_image, and every image there after is half the size until 1x1.
    """

    original_dimensions = src_image.size

    image_is_power_of_2 = is_power_of_2(original_dimensions[0]) and is_power_of_2(original_dimensions[1])
    if image_is_power_of_2 is False:
        print("Skipping image as dimensions are not power of 2")
        return None

    mips = []
    mips.append(src_image)

    current_size = original_dimensions
    while current_size != (1,1):
        current_size = halve_image_dimensions(current_size)

        # Create the new MipMap with the current size, using high quality downsampling
        newMip = src_image.resize(current_size, PIL.Image.LANCZOS)
        mips.append(newMip)

    return mips
