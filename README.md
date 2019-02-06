# MiSTer-NeoGeo-Romset-Parser

Extracts the relevant NeoGeo rom files (p-roms, s-roms and c-roms) from a zipped NeoGeo romset and generates
the romsets.xml file which is needed by the NeoGeo MiSTer core.

The source romset needs to be a non-merged or merged set. If a merged set is used then only the parent rom will get extracted.

Program roms in the .bin format are renamed so they can be visible inside the NeoGeo MiSTer core's OSD.

## Tools Included

**buildMiSTerNeoGeoRomset.py** 

usage: buildMiSTerNeoGeoRomset.py [-h] [-i SOURCE_FOLDER] [-o OUTPUT_FOLDER]

`-i` (or `--input_folder`) is the folder containing the source ROM set (from MAME / FBA)

`-o` (or `--output_folder`) is the folder in which to build the ROM set ready to be copied to /media/fat/neogeo

## Requirements

[python](https://www.python.org) 3.7 or newer

Linux, MacOS, or Windows
