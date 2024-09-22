import shutil
import string
from os import makedirs, listdir
from os.path import splitext, exists, isfile, join
from random import choices
from typing import TextIO
from pathlib import Path


class FileHandler:
    def __init__(self, file_name: str):
        self._file_name = file_name
        self._only_name, self._only_extension = splitext(file_name)
        self._files: list[TextIO] = []
        self._temp_folder = None
    
    def is_json(self) -> bool:
        return self._only_extension == '.json'
    
    def is_zip(self) -> bool:
        return self._only_extension == '.zip'
    
    def clean_up(self) -> None:
        for file in self._files:
            file.close()
            
        if self._temp_folder is not None:
            shutil.rmtree(self._temp_folder, ignore_errors=True)

    def get_file_content(self) -> list[TextIO]:
        self._files = []
        if self.is_json():
            self._files.append(open(self._file_name, 'r', encoding="utf-8"))
        elif self.is_zip():
            folder = self._make_random_folder() + '/'
            shutil.unpack_archive(self._file_name, folder)
            files = [f for f in listdir(folder) if isfile(join(folder, f))]
            for file_key, file_name in enumerate(files):
                only_name, only_extension = splitext(file_name)
                if only_extension == '.json':
                    self._files.append(open(folder + file_name, 'r', encoding="utf-8"))
        else:
            raise Exception("il file non è né un file zip, né un file json.")

        return self._files

    def _make_random_folder(self) -> str:
        path = Path(self._file_name)
        base_path = str(path.parent)
        while True:
            self._temp_folder = base_path + '/' + self._get_random_string()
            if not exists(self._temp_folder):
                makedirs(self._temp_folder)
                return self._temp_folder

    def _get_random_string(self) -> str:
        return ''.join(choices(string.ascii_uppercase + string.digits, k=8))
