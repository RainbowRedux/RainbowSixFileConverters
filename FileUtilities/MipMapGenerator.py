"""Utilities to help working with images"""

import logging
from typing import Tuple, Union, List, Optional

from PIL import Image as PILImage # type: ignore

log = logging.getLogger(__name__)

def is_power_of_2(number: int) -> bool:
    """Checks if a number is a power of 2"""
    num1 = ((number & (number - 1)) == 0)
    return num1

def halve_image_dimensions(dimensions: Union[Tuple[int, ...], List[int]]) -> Tuple[int, ...]:
    """
    Halves image dimensions. Returns ints. No new dimension will be less than 1
    """
    new_dimensions_float: List[float] = [x/2 for x in dimensions]
    new_dimensions: List[int] = [int(x) for x in new_dimensions_float]
    new_dimensions = [max(x, 1) for x in new_dimensions]
    return tuple(new_dimensions)


def generate_mip_maps(src_image: PILImage.Image) -> Optional[List[PILImage.Image]]:
    """
    Generate a list of images suitable for use as MipMaps
    src_image should be a PIL.Image with Power Of 2 dimensions
    Returns list of images, 0th element being the src_image, and every image there after is half the size until 1x1.
    """

    original_dimensions = src_image.size

    image_is_power_of_2 = is_power_of_2(original_dimensions[0]) and is_power_of_2(original_dimensions[1])
    if image_is_power_of_2 is False:
        log.warning("Skipping image as dimensions are not power of 2")
        return None

    mips: List[PILImage.Image] = []
    mips.append(src_image)

    current_size: List[int] = list(original_dimensions)
    while current_size != [1,1]:
        current_size = list(halve_image_dimensions(current_size))

        # Create the new MipMap with the current size, using high quality downsampling
        newMip = src_image.resize(current_size, PILImage.LANCZOS)
        mips.append(newMip)

    return mips
