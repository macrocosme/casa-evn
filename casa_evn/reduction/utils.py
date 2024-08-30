import os
import copy


def check_end_character(string, character):
    if string != '':
        if string[-1] != character:
            string = f'{string}{character}'
    return string

def check_underscore(string):
    """Assure string ends with an underscore

    Parameter
    ---------
    string:str

    Returns
    -------
    string:str
    """
    return check_end_character(string, "_")

def check_slash(string):
    """Assure string ends with a slash

    Parameter
    ---------
    string:str

    Returns
    -------
    string:str
    """
    return check_end_character(string, "/")

def check_folder_exists_or_create(folder, return_folder=True):
    if not os.path.exists(folder):
        os.makedirs(folder)
    if return_folder:
        return folder
