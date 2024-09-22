#pyinstaller --onefile main.py result_sheet.py
import os.path
import sys
import zipfile

import ijson
from os import listdir
from os.path import isfile, join, splitext

from configuration import Configuration
from file_handler import FileHandler
from result_sheet import ResultSheet
from extracted_line import ExtractedLine


def quit_because(reason: str) -> None:
    print(reason)
    sys.exit()

# shutil.unpack_archive(filename[, extract_dir[, format[, filter]]])

def get_files(path: str) -> list[str]:
    files = [f for f in listdir(path) if isfile(join(path, f))]
    files = reorder_files(files)
    for file_key, file_name in enumerate(files):
        files[file_key] = path + file_name

    print('Trovato ' + str(len(files)) + ' files nella cartella cig.')
    if len(files) == 0:
        raise Exception("Impossibile continuare, deve esserci almeno un file json.")

    return files


def reorder_files(files: list[str]) -> list[str]:
    reordable_files = []
    not_reordable_files = []
    for file in files:
        year = file[0:4]
        month = file[4:6]
        day = file[6:8]
        if year.isnumeric() and month.isnumeric() and day.isnumeric():
            reordable_files.append(file)
        else:
            not_reordable_files.append(file)
    
    reordable_files.sort(reverse=True)
    
    return reordable_files + not_reordable_files
            

def process_secondary_files(result_sheet: ResultSheet, path: str):
    files_name = get_files(path)
    line = {}
    for file_key, file_name in enumerate(files_name):
        file_handler = FileHandler(file_name)
        try:
            file_content = file_handler.get_file_content()
        except Exception as e:
            print('Salto il file ' + str(file_key + 1) + ' di ' + str(len(files_name)) + ': ' + file_name
                  + ' perchè ' + e.__str__())
            file_handler.clean_up()
            continue

        # Multiple ones because in case of a zip we assume inside there may be more than one json
        for single_content in file_content:
            parser = ijson.parse(single_content, multiple_values=True)
            print('Processo il file ' + str(file_key + 1) + ' di ' + str(len(files_name)) + ': ' + file_name)
            added_lines = 0
            for prefix, event, value in parser:
                if event == 'start_map':
                    line = {}
                elif prefix != '':
                    line[prefix] = value
                elif event == 'end_map':
                    result_sheet.add_not_cig_line(line, path[:-1])
                    added_lines += 1
            if added_lines > 0:
                sys.stdout.write('\n')
                sys.stdout.flush()

        file_handler.clean_up()

def execute(config: Configuration) -> None: 
    path_cig = config.get_cig_folder() + '/'
    if not os.path.isdir(path_cig):
        raise Exception('Errore, cartella dei CIG "' + config.get_cig_folder() + '" non trovata')
    
    path_others = []
    other_folders = config.get_other_folders()
    for folder in other_folders:
        if not os.path.isdir(folder):
            print('Attenzione, cartella "' + folder + '" non trovata.')
        else:
            path_others.append(folder + '/')

    result_sheet = ResultSheet(config)
    
    # CIG files ingest
    files_name = get_files(path_cig)
    line_counter = 1
    line = ExtractedLine(str(line_counter))
    for file_key, file_name in enumerate(files_name):
        file_handler = FileHandler(file_name)
        try:
            file_content = file_handler.get_file_content()
        except Exception as e:
            print('Salto il file ' + str(file_key + 1) + ' di ' + str(len(files_name)) + ': ' + file_name
                  + ' perchè ' + e.__str__())
            file_handler.clean_up()
            continue
        
        # Multiple ones because in case of a zip we assume inside there may be more than one json
        for single_content in file_content:
            parser = ijson.parse(single_content, multiple_values=True)
            print('Processo il file ' + str(file_key + 1) + ' di ' + str(len(files_name)) + ': ' + file_name)
            added_lines = 0
            for prefix, event, value in parser:
                if event == 'start_map':
                    line = ExtractedLine(str(line_counter))
                elif prefix != '':
                    line.add(prefix, value)
                elif event == 'end_map':
                    if line.has('cf_amministrazione_appaltante', config.get_cf_amministrazione()):
                        result_sheet.add_line(line, file_name)
                        line_counter += 1
                        added_lines += 1
            if added_lines > 0:
                sys.stdout.write('\n')
                sys.stdout.flush()

        file_handler.clean_up()

    # Process secondary files, data will be appended to the previously created lines
    for path in path_others:
        process_secondary_files(result_sheet, path)

    result_sheet.close_file()


if __name__ == '__main__':
    config = Configuration()
    if config.get_debug_mode():
        execute(config)
    else:
        try:
            execute(config)
        except Exception as error:
            print(error)
    
    print('\nPremere invio per terminare.')
    input()
        
