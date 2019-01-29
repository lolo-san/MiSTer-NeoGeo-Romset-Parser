# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#       buildMiSTerNeoGeoRomset.py
#       loloC2C - SmokeMonster discord 2019
#-------------------------------------------------------------------------------


# ------------------------------ import ----------------------------------------

import os
import argparse
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
import shutil

#-------------------------------------------------------------------------------

# tree = ET.parse('neogeo-mamedb.xml')
# root = tree.getroot()

# for software in root.findall('software'):
# 	print(software.get('name'))

# ------------------------------ code ------------------------------------------

parser = argparse.ArgumentParser(description="extract relevant neogeo rom files and generates romsets.xml file")
parser.add_argument("-i", "--input_folder", dest="source_folder", required=False, default=".", help="set source folder")
parser.add_argument("-o", "--output_folder", dest="output_folder", required=False, default=".", help="set output folder")
ARGS = parser.parse_args()

source_folder = os.path.normpath(ARGS.source_folder)
output_folder = os.path.normpath(ARGS.output_folder)

if not os.path.exists(output_folder):
	os.makedirs(output_folder)

romsets = ET.Element('romsets')
for filename in os.listdir(source_folder):
	filepath = os.path.join(source_folder, filename)

	if not zipfile.is_zipfile(filepath):
		continue

	directory = filename[:-4]

	need_rename = False
	has_prom = False
	has_crom = False
	has_srom = False
	extract_list = []

	zip_ref = zipfile.ZipFile(filepath, 'r')
	for entry in zip_ref.namelist():
		if zip_ref.getinfo(entry).is_dir() is True or entry.find("/") != -1:
			continue

		dot_index = entry.find(".")
		if entry[-4:] == ".bin" or entry[-4:] == ".rom":
			# Hack for Riding Hero
			if entry[dot_index-3:dot_index] == "com":
				continue

			entry_type = entry[dot_index-2:dot_index]
			need_rename = True
		else:
			entry_type = entry[dot_index+1:]

		if (entry_type[0] == "p" and entry_type[1].isnumeric()) or (entry_type[:2] == "ep" and entry_type[2].isnumeric()):
			extract_list.append(entry)
			has_prom = True
		elif entry_type[0] == "c" and entry_type[1].isnumeric():
			extract_list.append(entry)
			has_crom = True
		elif entry_type[0] == "s" and entry_type[1].isnumeric():
			extract_list.append(entry)
			has_srom = True

	if has_prom is False and (has_crom is False or has_srom is False):
		print(filename+" is not a valid neogeo rom file")
		zip_ref.close()
		continue

	rom_directory = os.path.join(output_folder, directory)
	for entry in extract_list:
		zip_ref.extract(entry, rom_directory)
		if need_rename is True:
			dot_index = entry.find(".")
			new_name = entry[:-3] + entry[dot_index-2:dot_index]
			oldname_path = os.path.join(rom_directory, entry)
			newname_path = os.path.join(rom_directory, new_name)
			if os.path.exists(newname_path):
				os.remove(oldname_path)
			else:
				os.rename(oldname_path, newname_path)

	zip_ref.close()

	p_file = []
	s_file = []
	c_files = []

	romset = ET.SubElement(romsets, 'romset')
	romset.set('name', directory)

	for romfile in os.listdir(rom_directory):
		romfile_path = os.path.join(rom_directory, romfile)
		romfile_size = os.path.getsize(romfile_path)
		if romfile[-3:] == ".p1" or  romfile[-4:] == ".ep1":
			p_file = [romfile, romfile_size]
		elif romfile[-3:-1] == ".s":
			s_file = [romfile, romfile_size]
		elif romfile[-3:-1] == ".c":	
			c_files.append([romfile, romfile_size])

	if p_file[1] > 0X100000:
		ET.SubElement(romset, 'file', attrib={'name': p_file[0], 'type': '0', 'index': '1', 'start': '0x100000', 'size': '0x100000'})
		ET.SubElement(romset, 'file', attrib={'name': p_file[0], 'type': '0', 'index': '2', 'start': '0', 'size': '0x100000'})
	else:
		size_value = "{0:#x}".format(p_file[1])
		ET.SubElement(romset, 'file', attrib={'name': p_file[0], 'type': '0', 'index': '1', 'start': '0', 'size': size_value})
	
	if len(s_file) > 0:
		size_value = "{0:#x}".format(s_file[1])
		ET.SubElement(romset, 'file', attrib={'name': s_file[0], 'type': '1', 'index': '3', 'start': '0', 'size': size_value})
	
	index = 32
	count = 0
	for c_file in c_files:
		final_index = index
		if (count & 1) == 0:
			final_index += 1
		else:
			final_index -= 1

		romfile_name = c_file[0]
		romfile_size = c_file[1]
		index_value = "{0:d}".format(final_index)
		size_value = "{0:#x}".format(romfile_size)
		ET.SubElement(romset, 'file', attrib={'name': romfile_name, 'type': '2', 'index': index_value, 'start': '0', 'size': size_value})

		count += 1
		index += 1
		if (count & 1) == 0:
			index -= 2
			index += int(romfile_size / (256*1024))
			
xml_str = minidom.parseString(ET.tostring(romsets)).toprettyxml(indent="    ", encoding='utf8')
xml_path = os.path.join(output_folder, "romsets.xml")

f = open(xml_path, "w")
f.write(xml_str.decode('utf8'))
f.close()
