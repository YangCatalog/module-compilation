# Copyright The IETF Trust 2021, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Slavomir Mazur"
__copyright__ = "Copyright The IETF Trust 2021, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "slavomir.mazur@pantheon.tech"


import glob
import os


def invert_yang_modules_dict(in_dict: dict, debug_level: int = 0):
    """
    Invert the dictionary of
        key:RFC/Draft file name,
        value:list of extracted YANG models
    into a dictionary of
        key:YANG model,
        value:RFC/Draft file name

    Arguments:
        :param in_dict      (dict) input dictionary
        :param debug_level  (int) debug level; If > 0 print some debug statements to the console
    :return: inverted output dictionary
    """
    if debug_level > 0:
        print('DEBUG: invert_yang_modules_dict: dictionary before inversion:\n{}'.format(str(in_dict)))

    inv_dict = {}
    for key, value in in_dict.items():
        for yang_model in in_dict[key]:
            inv_dict[yang_model] = key

    if debug_level > 0:
        print('DEBUG: invert_yang_modules_dict: dictionary after inversion:\n{}'.format(str(inv_dict)))

    return inv_dict


def remove_invalid_files(directory: str, yang_dict: dict):
    """
    Remove YANG modules in directory having invalid filenames.
    The root cause may be that XYM extracting YANG modules with non valid filename.

    Arguments:
        :param directory    (str) the directory to analyze for invalid filenames of extracted modules
        :param yang_dict    (dict) dictionary of key:extracted YANG modul name, value:RFC/Draft file name
    """
    path = '{}*.yang'.format(directory)
    for full_path in glob.glob(path):
        filename = os.path.basename(full_path)
        if ' ' in filename:
            os.remove(full_path)
            if yang_dict.get(filename):
                yang_dict.pop(filename)
            print('Invalid YANG module removed: {}'.format(full_path))
        if '@YYYY-MM-DD' in filename:
            os.remove(full_path)
            if yang_dict.get(filename):
                yang_dict.pop(filename)
            print('Invalid YANG module removed: {}'.format(full_path))
        if filename.startswith('.yang'):
            os.remove(full_path)
            if yang_dict.get(filename):
                yang_dict.pop(filename)
            print('Invalid YANG module removed: {}'.format(full_path))
        if filename.startswith('@'):
            os.remove(full_path)
            if yang_dict.get(filename):
                yang_dict.pop(filename)
            print('Invalid YANG module removed: {}'.format(full_path))


def check_after_xym_extraction(filename: str, extracted_yang_models: list):
    """
    Check whether name of the extracted yang model is valid.

    Arguments:
        :param filename                 (str) Filename of RFC/Draft file
        :param extracted_yang_models    (list) List of all the extracted models from RFC/Draft file
    """
    correct = True
    if any(' ' in extracted_model for extracted_model in extracted_yang_models):
        print('File {} contains module with invalid name [{}]'.format(filename, ', '.join(extracted_yang_models)))
        correct = False
    if any('YYYY-MM-DD' in extracted_model for extracted_model in extracted_yang_models):
        print('File {} contains module with invalid revision [{}]'.format(filename, ', '.join(extracted_yang_models)))
        correct = False
    if any('.yang' == extracted_model for extracted_model in extracted_yang_models):
        print('File {} contains module with missing name [{}]'.format(filename, ', '.join(extracted_yang_models)))
        correct = False

    return correct
