# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#       buildMiSTerNeoGeoRomset.py
#       loloC2C - SmokeMonster discord 2019
#-------------------------------------------------------------------------------

import os
import argparse
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
import shutil

def parse_args():
	parser = argparse.ArgumentParser(description="extract relevant neogeo rom files and generates romsets.xml file")
	parser.add_argument("-i", "--input_folder", dest="source_folder", required=False, default=".", help="set source folder")
	parser.add_argument("-o", "--output_folder", dest="output_folder", required=False, default=".", help="set output folder")
	return parser.parse_args()

def parse_database():
	db = {}
	root = ET.parse('neogeo-all.db').getroot()
	for software in root.findall('software'):
		db[software.get('name')] = software
	return db

def parse_software(db_entry):
	rom_infos = []
	for data in db_entry.find('part').findall('dataarea'):
		if any(unsupported in data.get('name') for unsupported in ("mcu", "audiocrypt", "audiocpu", "ymsnd", "ymsnd.deltat")):
			continue
		for rom in data.findall('rom'):
			flag = rom.get('loadflag')
			if flag != None and any(f in flag for f in ("fill", "ignore")):
				continue
			if flag == "continue":
				info = {'type': data.get('name'), 'name': rom_infos[-1].get('name'), 'size': rom.get('size'), 'offset': rom.get('offset'), 'flag': True}
			else:
				info = {'type': data.get('name'), 'name': rom.get('name'), 'size': rom.get('size'), 'offset': rom.get('offset'), 'flag': False}
			rom_infos.append(info)
	return rom_infos

def get_software_list(romfiles):
	sl = []
	nb = 0
	for rf in romfiles:
		nb += 1
		if rf.get('flag') is True:
			continue
		if nb & 1 == 0 and rf.get('type') == "maincpu" and int(rf.get('size'), 16) < 0x100000:
			sl.pop()
			sl.append((romfiles[nb-2].get('name'), rf.get('name')))
		else:
			if nb == 1 and rf.get('type') == "maincpu" and rf.get('name')[-3:] == "bin":
				sl.append((rf.get('name'), "rename"))
			else:
				sl.append((rf.get('name'), ""))
	return sl

def copy_zip_software(output_folder, output_name, romfiles, dirpath, filename):
	softpath = os.path.join(dirpath, filename)
	zip_ref = zipfile.ZipFile(softpath, 'r')
	s_list = get_software_list(romfiles)
	for entry in s_list:
		if any(f in entry[0] for f in zip_ref.namelist()) is False:
			print("could not find rom "+entry[0]+" in "+softpath)
			return
		elif entry[1] != "" and entry[1] != "rename" and any(f in entry[1] for f in zip_ref.namelist()) is False:
			print("could not find rom "+entry[1]+" in "+softpath)
			return

	output_path = os.path.join(output_folder, output_name)
	if not os.path.exists(output_path):
		os.makedirs(output_path)

	for entry in s_list:
		if entry[1] == "":
			zip_ref.extract(entry[0], output_path)
		elif entry[1] == "rename":
			f = open(os.path.join(output_path, entry[0]), 'wb')
			f.write(zip_ref.read(entry[0]))
			f.close()
		else:
			f = open(os.path.join(output_path, entry[0]), 'wb')
			f.write(zip_ref.read(entry[0])+zip_ref.read(entry[1]))
			f.close()

	zip_ref.close()

def copy_dir_software(output_folder, romfiles, dirpath, dirname):
	softpath = os.path.join(dirpath, dirname)
	print("found dir at "+softpath)

	s_list = get_software_list(romfiles)
	for entry in s_list:
		print(entry)

	if not os.path.exists(folder):
		os.makedirs(folder)

def generate_romsets_info(folder, software_list):
	if not os.path.exists(folder):
		os.makedirs(folder)

	romsets = ET.Element('romsets')

	rom_type = {'maincpu': '0', 'fixed': '1', 'sprites': '2'}
	for entry in software_list:
		romset = ET.SubElement(romsets, 'romset')
		romset.set('name', entry[0])

		rom_list = entry[1]
		rom_cpu_list = []
		rom_fix_list = []
		rom_spr_list = []
		for rom in rom_list:
			if rom['type'] == "maincpu":
				rom_cpu_list.append(rom)
			elif rom['type'] == "fixed":
				rom_fix_list.append(rom)
			elif rom['type'] == "sprites" and rom['flag'] is False:
				rom_spr_list.append(rom)

		for rom in rom_list:
			if rom['type'] == "sprites" and rom['flag'] is True:
				rom_spr_list.append(rom)

		# maincpu rom files - look for concatenation
		concatenate = False
		rom_size = 0
		for rom in rom_cpu_list:
			rom_size += int(rom.get('size'), 16)

		if len(rom_cpu_list) == 2 and rom_size <= 0x100000:
			concatenate = True

		# maincpu rom files
		index = 1
		for rom in rom_cpu_list:
			rom_offs = rom.get('offset')
			if index > 1:
				rom_offs = "0"

			if concatenate is True:
				size = "{0:#x}".format(rom_size)
			else:
				size = rom.get('size')
			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
													'type': rom_type.get(rom['type']),
													'index': "{0:d}".format(index),
													'start': rom_offs,
													'size': size})
			if index == 2 or concatenate is True:
				break
			index += 1

		# fixed rom files
		index = 3
		for rom in rom_fix_list:
			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
													'type': rom_type.get(rom['type']),
													'index': "{0:d}".format(index),
													'start': rom.get('offset'),
													'size': rom.get('size')})

		# sprites rom files
		for rom in rom_spr_list:
			rom_offs = rom.get('offset')
			offset = int(rom_offs, 16)
			if offset & 1 == 0:
				index = 33
			else:
				offset -= 1
				index = 32
			index += int(offset / (512*1024))

			if rom['flag'] is False:
				rom_offs = "0"
			else:
				rom_offs = rom.get('size')

			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
													'type': rom_type.get(rom['type']),
													'index': "{0:d}".format(index),
													'start': rom_offs,
													'size': rom.get('size')})

	xml_str = minidom.parseString(ET.tostring(romsets)).toprettyxml(indent="    ", encoding='utf8')
	xml_path = os.path.join(folder, "romsets.xml")

	f = open(xml_path, "w")
	f.write(xml_str.decode('utf8'))
	f.close()

if __name__ == '__main__':

	ARGS = parse_args()
	db = parse_database()

	source_folder = os.path.normpath(ARGS.source_folder)
	output_folder = os.path.normpath(ARGS.output_folder)

	software_list = []
	sorted_files = sorted(os.walk(source_folder))
	for dirpath, dirnames, filenames in sorted_files:
		if filenames:
			filenames.sort()
			for f in filenames:
				if f[-4:] == ".zip" and f[:-4] in db:
					rom_infos = parse_software(db.get(f[:-4]))
					software_list.append((f[:-4], rom_infos))
					copy_zip_software(output_folder, f[:-4], rom_infos, dirpath, f)

		if dirnames:
			dirnames.sort()
			for d in dirnames:
				if d in db:
					rom_infos = parse_software(db.get(d))
					software_list.append((d, rom_infos))
					copy_dir_software(output_folder, rom_infos, dirpath, d)

	if len(software_list) > 0:
		generate_romsets_info(output_folder, software_list)
