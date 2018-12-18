# RainbowSixFileConverters

These collection of python scripts will allow you to extract data from Rainbow Six, Eagle Watch and Rogue Spear.

## Requirements

- Python 3.6 & 3.7
- Pillow 5.0 is required for the RSB conversion utility

## Notes on file formats and code

In almost all of the converters there are several fields which are unknown. These are stored in the classes as well as in the accompanying JSON files, and are labelled in ascending order, such as "unknown1". I've tried to account for later versions of the files even though i'm not focusing on those versions for this project, so these field names/numbers will still be taken into account.

For the avoidance of confusing, the shorthand abreviations and prefixes that are used in code are:

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

Highly recommend the user of virtualenvwrapper. Currently paths are hardcoded into the python files, this will change ASAP. for now look near the bottom of the Converter.py scripts and add your path by changing the following lines:

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

### Blender Usage

Coming soon. It's a bit hacky at the moment. File an issue, and I'll work on this sooner.

## Special Thanks

This project is made much easier thanks to the information published by Alexander Evdokimov (https://github.com/AlexKimov), at https://github.com/AlexKimov/RSE-file-formats.
