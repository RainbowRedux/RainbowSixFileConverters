# RainbowSixFileConverters
These collection of python scripts will allow you to extract data from Rainbow Six, Eagle Watch and Rogue Spear.

# Requirements
- Python 2.7 or Python 3.6
- Pillow 5.0 is required for the RSB conversion utility

# Notes on file formats and code
In almost all of the converters there are several fields which are unknown. These are stored in the classes as well as in the accompanying JSON files, and are labelled in ascending order, such as "unknown1". I've tried to account for later versions of the files even though i'm not focusing on those versions for this project, so these field names/numbers will still be taken into account.

# Special Thanks
This project is made much easier thanks to the information published by Alexander Evdokimov (https://github.com/AlexKimov), at https://github.com/AlexKimov/RSE-file-formats.
