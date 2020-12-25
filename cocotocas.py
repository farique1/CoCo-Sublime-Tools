#!/usr/bin/env python3
"""
CoCo to CAS
Beta Version
Convert BAS, ASC or BIN files to CAS.

Copyright (C) 2020 - Fred Rique (farique)

For help use:
cocotocas.py -h
"""

import os
import binascii
import argparse

file_load = ''
file_save = ''
file_format = ''

parser = argparse.ArgumentParser(description='Convert CoCo programs to .cas format. Guess input format based on extension, can be forced with -ff.')
parser.add_argument("input", nargs='?', default=file_load, help='File to convert')
parser.add_argument("output", nargs='?', default=file_save, help='.cas file to export')
parser.add_argument("-ff", default=file_format, choices=['bas', 'BAS', 'bin', 'BIN', 'asc', 'ASC'], help="Override type: bas, bin, asc")
args = parser.parse_args()

file_load = args.input
file_save = args.output
file_format = args.ff

bin_file = []               # Loaded file
cas_file = ''               # Export file
b_leader = '55' * 127       # Sync gap. Last '55' on b_magic_bytes
b_magic_bytes = '55553c'    # Magic bytes
b_block_type = '00'         # 00=filename, 01=data, FF=EOF
b_file_type = '00'          # 00=BASIC, 01=data, 02=machine code
b_ascii_flag = '00'         # 00=binary, FF=ASCII
b_gap_flag = '00'           # 00=no gaps, FF=gaps
b_exec_addrs = '0000'       # Machine code start address
b_strt_addrs = '0000'       # Machine code load address
b_chksum = '00'             # Block checksum byte
b_block_len = '00'          # Block length
b_filename = '02' * 8       # Filename

file_ext = os.path.splitext(file_load)[1][1:].lower() if file_format == '' else file_format.lower()
file_save = file_load if file_save == '' else file_save
file_path = os.path.split(os.path.realpath(file_save))[0]
file_name = os.path.split(os.path.splitext(file_save)[0])[1]
file_save = file_path + '/' + file_name + '.cas'

if file_load == '':
    print('*** No file given.')
    raise SystemExit(0)

if not os.path.isfile(file_load):
    print('*** File not found.')
    raise SystemExit(0)

if file_ext == '':
    print('*** No extension or override given.')
    raise SystemExit(0)


def bytes_from_file(filename, chunksize=8192):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                for b in chunk:
                    yield b
            else:
                break


def get_checksum(string):
    chksum = 0
    for (l, h) in zip(string[0::2], string[1::2]):
        byte = int(l + h, 16)
        chksum = (chksum + byte) % 256
    return '{0:02x}'.format(chksum)


for b in bytes_from_file(file_load):
    bin_file.append('{0:02x}'.format(b))

if file_ext == 'bas' and bin_file[0] == 'ff':
    del bin_file[:3]

# Filename Block
b_block_type = '00'     # filename block
b_block_len = '0f'      # filename block length
b_filename = ''.join(['{0:02x}'.format(ord(elem)) for elem in file_name[:8].upper()])
b_filename += '20' * ((16 - len(b_filename)) // 2)
b_file_type = '00' if file_ext == 'bas' or file_ext == 'asc' else '02' if file_ext == 'bin' else '01'
b_ascii_flag = '00' if file_ext == 'bas' or file_ext == 'bin' else 'ff'
b_gap_flag = '00' if file_ext == 'bas' or file_ext == 'bin' else 'ff'
if file_ext == 'bin':
    # Byte 1 and 2 file size, byte 3 and 4 start address, last two bytes exec address
    b_strt_addrs = ''.join(bin_file[3:5])  # bytes 3 and 4
    b_exec_addrs = ''.join(bin_file[-2:])  # last two bytes
    del bin_file[:5]
block_filename = b_block_type + b_block_len + b_filename + \
    b_file_type + b_ascii_flag + b_gap_flag + b_exec_addrs + b_strt_addrs
b_chksum = get_checksum(block_filename)
cas_file = b_leader + b_magic_bytes + block_filename + b_chksum + b_leader
b_leader = '' if b_gap_flag == '00' else b_leader

# Data Block
b_block_type = '01'  # data block
pointer = 0
data_block_len = 255
while data_block_len == 255:
    data_block = bin_file[pointer:pointer + 255]
    data_block_len = len(data_block)
    b_block_len = '{0:02x}'.format(data_block_len)
    block_chksum = b_block_type + b_block_len + ''.join(data_block)
    b_chksum = get_checksum(block_chksum)
    block_data = b_magic_bytes[2:] + block_chksum + b_chksum
    cas_file += block_data + b_leader
    pointer += 255

# EOF Block
b_block_type = 'ff'  # EOF block
b_block_len = '00'  # EOF block length
b_chksum = 'ff'  # EOF block checksum
cas_file += b_magic_bytes + b_block_type + b_block_len + b_chksum + b_magic_bytes[:2]

with open(file_save, 'wb') as f:
    for (l, h) in zip(cas_file[0::2], cas_file[1::2]):
        f.write(binascii.unhexlify(l + h))
