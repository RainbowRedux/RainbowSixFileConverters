# RainbowSixFileConverters

These collection of python scripts will allow you to extract data from Rainbow Six, Eagle Watch and Rogue Spear.

[![CodeFactor](https://www.codefactor.io/repository/github/rainbowredux/rainbowsixfileconverters/badge)](https://www.codefactor.io/repository/github/rainbowredux/rainbowsixfileconverters)
![mypy](https://github.com/RainbowRedux/RainbowSixFileConverters/workflows/Mypy%20Type%20Check%20Analysis/badge.svg)

## Discord

If you'd like to follow this project or help out, please join the discord channel at https://discord.gg/YygR4S8

Discussions of other projects related to older RSE games is also welcome.

## Wiki

Currently the wiki is being filled out with information, make sure to check here for additional info.
https://github.com/boristsr/RainbowSixFileConverters/wiki

## Packages
This project consists of several python packages.

- RainbowFileReaders - This package is dedicated to reading the Files from Rainbow Six, Rogue Spear and other Red Storm Entertainment games.
- FileUtilities - This package consists of a few utility classes which are used in RainbowFileReaders
- BlenderImporters - This package uses RainbowFileReaders to read files and then imports the data to Blender. Blender specific code resides here.

## Requirements

### RainbowFileReaders

- Python 3.6 & newer
- Pillow 5.0 is required for the RSB conversion utility

### BlenderImporters

- Blender 2.8

## Notes on file formats and code

In almost all of the converters there are several fields which are unknown. These are stored in the classes as well as in the accompanying JSON files, and are labelled in ascending order, such as "unknown1". I've tried to account for later versions of the files even though i'm not focusing on those versions for this project, so these field names/numbers will still be taken into account.

For the avoidance of confusion, the shorthand abreviations and prefixes that are used in code are:

- **RSE** - Red Storm Entertainment, shared data structures, or datastructures that can be conformed easily with a few variations between versions
- **R6** - Rainbow Six, Eagle Watch. The first game and mission pack in the series
- **RS** - Rogue Spear, Urban Operations, (possibly Covert Ops Essentials). The second game in the series.

There are also prefixes for specific formats, like SOB, MAP, etc. These match the file extension of the file types that these datastructures appear in.

If a datastructure is specific to game version, but used in many files, it will contain a game prefix. If it's specific to a file type, it will contain a type prefix. If it is specific to a game and filetype, it will contain both.

\[GamePrefix\]\[FiletypePrefix\]DataStructure

## Status of specific formats

Please refer to the [wiki](https://github.com/boristsr/RainbowSixFileConverters/wiki)

## Usage

### Commandline

I highly recommend the use of virtualenvwrapper.

Currently the gamepath is defined in settings.json. Most of the tools should reference this.

```python
paths = []
paths.append("../Data/Test")
```

To setup the environment and run the scripts, run the following commands

```shell
mkvirtualenv -p python3 rainbow
workon rainbow
pip install pillow
python RSBtoPNGConverter.py
python SOBtoOBJConverter.py
```

### List of provided commandline tools

- MapConverter.py - Reads all maps and writes a plain text JSON to show the data in the file. Useful for learning the structure of maps.
- RSBPNGCacheGenerator.py - Converts all RSBs to PNGs, with the suffix .CACHE.PNG. References the relevant CXP files to apply the alpha key. Single Threaded.
- RSBtoPNGConverter.py - Converts all RSBs to PNGs. Does not reference CXP file, so no alpha keys are converted. Writes meta data to a JSON file beside the PNG. Uses multiprocessing.
- SOBtoOBJConverter.py - Converts SOB files to OBJ files. OBJ doesn't support all data, so some data is lost in the process.
- gameLoadTest.py - Uses RSEGameLoader to load a game and list missions. Will be expanded to test loading mods as well.

### Blender Usage

Coming soon. It's a bit hacky at the moment and the tools need a bit of love as Unreal has been the focus recently. If you would like some help with these, please file an issue or jump on discord and I'll help you out.

## Special Thanks

This project is made much easier thanks to the information published by Alexander Evdokimov (https://github.com/AlexKimov), at https://github.com/AlexKimov/RSE-file-formats.
