#!/usr/bin/env python3
"""
CoCo Badig Build
Beta Version
A Sublime 3 build system to convert CoCo Basic Dignified to traditional CoCo Basic and run on XRoar
or tokenize and run ASCII CoCo Basic on XRoar.

Copyright (C) 2020 - Fred Rique (farique)

Installation notes on the README.md or readme.txt
"""

import os.path
import argparse
import subprocess
import configparser
from os import remove as osremove

cocobadig_filepath = ''     # Path to CoCo Basic Dignified ('' = local path)
decb_filepath = ''          # Path to Tool Shed's decb ('' = local path)
xroar_filepath = ''         # Path to XRoar ('' = local path)
xrconfig_name = ''          # Path to XRoar configuration to open, eg: 'xroarcp400.conf' 'xroarcoco2b.conf'
# xrconfig_name = '/Users/Farique/Dropbox/CoCo_MSX_Stuff/Consoles/XroarOSX/Misc/xroarcp400.conf'          # Path to XRoar configuration to open, eg: 'xroarcp400.conf' 'xroarcoco2b.conf'
tokenize = True             # Tokenize the ASCII code
tokenize_stop = True        # Stop the execution on tokenize errors (keeps the ASCII version)
verbose_level = 3           # Show processing status: 0-silent 1-+erros 2-+warnings 3-+steps 4-+details
show_output = True          # Show the XRoar stdout output


def show_log(line, text, level, **kwargs):
    bullets = ['', '*** ', '  * ', '--- ', '  - ', '    ']

    if line != '':
        line_num, line_alt, line_file = line
    else:
        line_num, line_file = '', ''

    show_file = [True, False]

    try:
        bullet = kwargs['bullet']
    except KeyError:
        bullet = level

    try:
        show_file = kwargs['show_file']
    except KeyError:
        show_file = False

    display_file_name = ''
    if show_file and line_file != '':
        display_file_name = included_dict[line_file] + ': '

    line_num = '(' + str(line_num) + '): ' if line_num != '' else ''

    if verbose_level >= level:
        print(bullets[bullet] + display_file_name + line_num + text)

    if bullet == 1 and not show_file:
        print('    Execution_stoped')
        print()
        raise SystemExit(0)


show_log('', 'CoCo Badig Build', 3, bullet=0)

parser = argparse.ArgumentParser(description='Convert CoCo Basic Dignified source and run on XRoar')
parser.add_argument("file_path", help='The path to the opened file to convert')
parser.add_argument("file_name", help='The opened file to convert')
parser.add_argument("-classic", action='store_true', help='The flavor of Basic to process')
parser.add_argument("-convert", action='store_true', help='Do not run the code after conversion')
parser.add_argument("-tokenize", default=tokenize, action='store_true', help='Tokenize the ASCII code')
parser.add_argument("-list", action='store_true', help='Save a .mlt list file')
args = parser.parse_args()

export_path = args.file_path + '/'
export_file = os.path.splitext(args.file_name)[0] + '.asc'
classic_basic = args.classic
convert_only = args.convert
tokenize = args.tokenize
file_load = args.file_name

local_path = os.path.split(os.path.abspath(__file__))[0] + '/'
if os.path.isfile(local_path + 'CoCo Badig Build.ini'):
    config = configparser.ConfigParser()
    config.sections()
    try:
        config.read(local_path + 'CoCo Badig Build.ini')
        cocobadig_filepath = config.get('DEFAULT', 'cocobadig_filepath') if config.get('DEFAULT', 'cocobadig_filepath') else cocobadig_filepath
        decb_filepath = config.get('DEFAULT', 'decb_filepath') if config.get('DEFAULT', 'decb_filepath') else decb_filepath
        xroar_filepath = config.get('DEFAULT', 'xroar_filepath') if config.get('DEFAULT', 'xroar_filepath') else xroar_filepath
        xrconfig_name = config.get('DEFAULT', 'xrconfig_name') if config.get('DEFAULT', 'xrconfig_name') else xrconfig_name
        tokenize = config.getboolean('DEFAULT', 'tokenize') if config.get('DEFAULT', 'tokenize') else tokenize
        tokenize_stop = config.getboolean('DEFAULT', 'tokenize_stop') if config.get('DEFAULT', 'tokenize_stop') else tokenize_stop
        verbose_level = config.getint('DEFAULT', 'verbose_level') if config.get('DEFAULT', 'verbose_level') else verbose_level
    except (ValueError, configparser.NoOptionError) as e:
        show_log('', '', 1, bullet=0)
        show_log('', 'CoCo Badig Build.ini: ' + str(e), 1)

valid_args = ['-ls', '-lp', '-lz', '-rh', '-cs', '-gs', '-uo', '-bl', '-lg', '-sl', '-ll', '-nr', '-cr',
              '-ki', '-nc', '-tg', '-of', '-vs', '-vb', '-frb', '-ini']
arg_num = len(valid_args)
arg = ['-frb'] * arg_num
arg[arg_num - 2] = '-vb=' + str(verbose_level)
disk_ext_slot = 'ext'
using_xrconfig = 'default config'
output = ''
decb_output = ''
arguments_line = ''
line_chama = ''
line_list = {}
included_dict = {}
if cocobadig_filepath == '':
    cocobadig_filepath = local_path + 'CoCoBadig.py'
if decb_filepath == '':
    decb_filepath = local_path + 'decb'
if xroar_filepath == '':
    xroar_filepath = local_path + 'XRoar.app'
cocotocas_filepath = local_path + 'CoCoToCas.py'

show_log('', ''.join(['Building ', args.file_path, '/', args.file_name]), 3, bullet=0)
show_log('', '', 3, bullet=0)
show_log('', ''.join([('Classic Basic' if classic_basic else 'Basic Dignified')]), 3)
if classic_basic:
    label_log = 'Tokenize only' if tokenize and convert_only else \
        'Tokenize and run' if tokenize and not convert_only else 'Run'
if not classic_basic:
    label_log = 'Convert only' if convert_only else 'Default'
show_log('', label_log, 3, bullet=5)

if not os.path.isfile(cocobadig_filepath) and not classic_basic:
    show_log('', ''.join(['CoCo_Basic_Dignified.py_not_found: ', cocobadig_filepath]), 1)  # Exit

# if not os.path.isfile(decb_filepath) and tokenize:
#     show_log('', ''.join(['decb_not_found: ', decb_filepath]), 1)  # Exit

if not os.path.isdir(xroar_filepath) and not convert_only:
    show_log('', ''.join(['XRoar_not_found: ', xroar_filepath]), 1)  # Exit

show_log('', '', 3, bullet=5)

if not classic_basic:
    with open(args.file_path + '/' + args.file_name, encoding='latin1') as f:
        for n, line in enumerate(f):
            if line.startswith('##BB:export_path='):
                export_path = line.replace('##BB:export_path=', '').strip()
                if export_path[-1:] != '/':
                    export_path += '/'
            if line.startswith('##BB:export_file='):
                export_file = line.replace('##BB:export_file=', '').strip()
            if line.startswith('##BB:convert_only='):
                convert_only = True if line.replace('##BB:convert_only=', '').lower().strip() == 'true' else False
            if line.startswith('##BB:override_config='):
                xrconfig_name = line.replace('##BB:override_config=', '').strip()
            if line.startswith('##BB:arguments='):
                arguments_line = n + 1
                arguments = line.replace('##BB:arguments=', '').strip()
                arguments = arguments.split(',')
                for num, item in enumerate(arguments):
                    if num > arg_num - 5:  # args [arg_num-4], [arg_num-3], [arg_num-2] and [arg_num-1] are reserved to -tt, -vb, -exe and -frb
                        break
                    item2 = item
                    item2 = item2.strip()
                    item2 = item2.replace(' ', '=')
                    if item2.split('=')[0] not in valid_args:
                        show_log('', ' '.join(['invalid_argument:', item2]), 1)
                    if item2.split('=')[0] == '-vb':
                        try:
                            verbose_level = int(item2.split('=')[1])
                        except IndexError:
                            show_log('', ' '.join(['invalid_argument_value:', '-vb']), 1)
                        arg[arg_num - 2] = item2
                        item2 = '-frb'
                    if item2.split('=')[0] == '-tt':
                        try:
                            tokenize_tool = item2.split('=')[1].upper()
                        except IndexError:
                            show_log('', ' '.join(['invalid_argument_value:', '-tt']), 1)
                        arg[arg_num - 3] = item2
                        item2 = '-frb'
                    arg[num] = item2

    args_token = list(set(arg))
    show_log('', 'CoCo Basic Dignified', 3, bullet=0)
    show_log('', ''.join(['Converting ', args.file_path, '/', args.file_name]), 3, bullet=0)
    show_log('', ''.join(['To ', export_path, export_file]), 3, bullet=0)
    show_log('', ''.join(['With args ', ' '.join(args_token)]), 3, bullet=0)
    try:
        chama = ['python3', '-u', cocobadig_filepath, args.file_path + '/' + args.file_name, export_path + export_file]
        chama.extend(arg)
        output = subprocess.check_output(chama, encoding='utf-8')
        for line in output:
            line_chama += line
            if line == '\n':
                if 'linelst-' in line_chama:
                    line_get = line_chama.replace('linelst-', '').split(',')
                    line_list[line_get[0]] = [line_get[1].rstrip(), line_get[2].rstrip()]
                elif 'export_file-' in line_chama:
                    export_file = line_chama.replace('export_file-', '').strip()
                elif 'includedict-' in line_chama:
                    included_get = line_chama.replace('includedict-', '').strip()
                    included_get = included_get.split(',')
                    included_dict[included_get[0]] = included_get[1]
                elif 'Tokenizing_aborted' in line_chama:
                    show_log('', line_chama.rstrip(), 1, bullet=0)
                    tokenize = False
                else:
                    show_log('', line_chama.rstrip(), verbose_level, bullet=0)
                line_chama = ''
        export_file = os.path.splitext(export_file)[0] + '.asc'

    except subprocess.CalledProcessError:
        show_log('', ''.join([args.file_name, ': (', str(arguments_line), '): argument_error']), 1)  # Exit

if xrconfig_name != '' and not os.path.isfile(xrconfig_name) and not convert_only:
    show_log('', ''.join(['XRoar_alternate_config_not_found: ', xrconfig_name]), 1)  # Exit

if xrconfig_name != '':
    using_xrconfig = xrconfig_name
    xrconfig_name = ['-c', xrconfig_name]

list_arg = ['-t'] * 1
out_line = ''
args_token = list(set(list_arg))
pre_args = '' if ''.join(args_token) else 'no '
show_log('', "ToolShed's decb tokenizer", 3, bullet=0)
show_log('', ''.join(['Converting ', export_path, export_file]), 3, bullet=0)
show_log('', ''.join(['To ', export_path, os.path.splitext(export_file)[0] + '.bas']), 3, bullet=0)
show_log('', ''.join(['With ', pre_args + 'args ', ' '.join(args_token)]), 3, bullet=0)
if os.path.isfile(decb_filepath):
    decb_cmd = [decb_filepath, 'copy', export_path + export_file,
                export_path + os.path.splitext(export_file)[0] + '.bas', list_arg[0]]
    decb_output = subprocess.check_output(decb_cmd, encoding='utf-8')
    for line in decb_output:
        out_line += line
        if line == '\n':
            show_log('', out_line.rstrip(), verbose_level, bullet=0)
            out_line = ''
    print ()
    export_file = os.path.splitext(export_file)[0] + '.bas'
else:
    show_log('', ''.join(['decb_not_found: ', decb_filepath]), 2)
    print()

if convert_only:
    raise SystemExit(0)


list_arg = [''] * 1
out_line = ''
args_token = list(set(list_arg))
pre_args = '' if ''.join(args_token) else 'no '
show_log('', "CoCo to CAS", 3, bullet=0)
show_log('', ''.join(['Converting ', export_path, export_file]), 3, bullet=0)
show_log('', ''.join(['To ', export_path, os.path.splitext(export_file)[0] + '.cas']), 3, bullet=0)
show_log('', ''.join(['With ', pre_args + 'args ', ' '.join(args_token)]), 3, bullet=0)
if os.path.isfile(cocotocas_filepath):
    try:
        cocotocas_cmd = ['python3', '-u', cocotocas_filepath, export_path + export_file, list_arg[0]]
        cocotocas_output = subprocess.check_output(cocotocas_cmd, encoding='utf-8')
        for line in cocotocas_output:
            out_line += line
            if line == '\n':
                show_log('', out_line.rstrip(), verbose_level, bullet=0)
                out_line = ''
        print ()
        export_file = os.path.splitext(export_file)[0] + '.cas'
    except subprocess.CalledProcessError:
        show_log('', ' '.join(['argument_error:', ''.join(args_token)]), 1)  # Exit
else:
    show_log('', ''.join(['CoCoToCas.py_not_found']), 2)

if not tokenize:
    osremove(export_path + export_file)


def output(show_output, output_text):
    fail_words = ['cannot open', 'failed to open', 'Invalid CRC']
    if show_output and output_text.strip() != '':
        if any(word in output_text for word in fail_words):
            output_text = output_text.replace('WARNING: ', '')
            proc.kill()
            show_log('', output_text.rstrip(), 1)  # Exit
        elif 'WARNING:' in output_text:
            output_text = output_text.replace('WARNING: ', '')
            show_log('', output_text.rstrip(), 2)
        elif output_text[:1] != '\t':
            show_log('', output_text.rstrip(), 3)
        else:
            show_log('', output_text.strip(), 4)


show_log('', 'XRoar', 3, bullet=0)
show_log('', ''.join(['Opeening ', export_path, export_file]), 3, bullet=0)
show_log('', ''.join(['With ', using_xrconfig]), 3, bullet=0)
show_log('', '', 3, bullet=0)

cmd = [xroar_filepath + '/Contents/MacOS/xroar']
if xrconfig_name != '':
    cmd.extend(xrconfig_name)
cmd.extend(['-run', export_path + export_file])
cmd.extend(['-v', '2', '-debug-file', '0x0004'])

proc = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
for line in iter(proc.stdout.readline, b''):
    output(show_log, line)
    poll = proc.poll()
    if poll is not None:
        print ()
        break

osremove(export_path + export_file)

show_log('', '', 1, bullet=0)
