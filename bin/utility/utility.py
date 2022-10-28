# Copyright The IETF Trust 2022, All Rights Reserved
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

__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'

import configparser
import glob
import os
import time
import typing as t
from datetime import date
from enum import Enum, auto

import dateutil.parser
import jinja2
from parsers import yang_parser
from pyang.statements import Statement
from redis_connections.redis_connection import RedisConnection
from utility.static_variables import IETF_RFC_MAP, NAMESPACE_MAP, ORGANIZATIONS
from versions import ValidatorsVersions

module_db = None
incomplete_db = None


class IETF(Enum):
    RFC = auto()
    DRAFT = auto()
    DRAFT_ARCHIVE = auto()
    EXAMPLE = auto()


def list_files_by_extensions(
    srcdir: str,
    extensions: t.Union[tuple[str], list[str]],
    return_full_paths: bool = False,
    recursive: bool = False,
    follow_links: bool = False,
    debug_level: int = 0,
) -> list[str]:
    """
    Returns the list of files in a directory with matching extensions.

    Arguments:
        :param srcdir: (str) directory to search for files
        :param extensions: (str) file extensions to search for
        :param return_full_paths: (bool) whether return a list of full paths to matching files or only filenames
        :param recursive: (bool) whether to search for files in subdirectories or not
        :param follow_links: (bool) set to true in order to follow symbolic links to subdirectories
        during the recursive search
        :param debug_level: (int) if greater than 0 - information about every file's extension will be printed
    :return: list of matching files
    """

    def check_filename_has_matching_extension(file_path: str, filename: str) -> bool:
        is_file = os.path.isfile(file_path)
        if not is_file:
            return False
        file_extension = filename.rsplit('.', 1)[-1]
        if file_extension in extensions:
            if debug_level > 0:
                print(f'DEBUG: "{file_path}" ends with {file_extension}')
            return True
        if debug_level > 0:
            print(f'DEBUG: "{file_path}" does not end with one of the extensions: {extensions}')
        return False

    matching_files = []
    if recursive:
        for root, _, filenames in os.walk(srcdir, followlinks=follow_links):
            for filename in filenames:
                path = os.path.join(root, filename)
                if not check_filename_has_matching_extension(path, filename):
                    continue
                matching_file = path if return_full_paths else filename
                matching_files.append(matching_file)
        return matching_files
    for filename in os.listdir(srcdir):
        path = os.path.join(srcdir, filename)
        if not check_filename_has_matching_extension(path, filename):
            continue
        matching_file = path if return_full_paths else filename
        matching_files.append(matching_file)
    return matching_files


def module_or_submodule(yang_file_path: str) -> t.Optional[str]:
    """
    Try to find out if the given model is a submodule or a module.

    Argument:
        :param yang_file_path   (str) Full path to the yang model to check
    """
    if os.path.isfile(yang_file_path):
        with open(yang_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        commented_out = False
        for each_line in all_lines:
            module_position = each_line.find('module')
            submodule_position = each_line.find('submodule')
            cpos = each_line.find('//')
            if commented_out:
                mcpos = each_line.find('*/')
            else:
                mcpos = each_line.find('/*')
            if mcpos != -1 and (cpos > mcpos or cpos == -1):
                if commented_out:
                    commented_out = False
                else:
                    commented_out = True
            if submodule_position >= 0 and (submodule_position < cpos or cpos == -1) and not commented_out:
                return 'submodule'
            if module_position >= 0 and (module_position < cpos or cpos == -1) and not commented_out:
                return 'module'
        print(f'File {yang_file_path} is not yang file or not well formated')
        return 'wrong file'
    return None


def dict_to_list(in_dict: dict, is_rfc: bool = False) -> list[list]:
    """Create a list out of compilation results from 'in_dict' dictionary variable.
    First element of each list is name of the module, second one is compilation-status
    which is followed by compilation-results.

    Argument:
        :param in_dict      (dict) Dictionary of modules with compilation results
        :param is_rfc       (bool) Whether we are transforming dictionary containing RFC modules
                                    - it has slightly different structure
    :return: List of lists of compilation results
    """
    if is_rfc:
        return [[key, value] for key, value in in_dict.items() if value is not None]
    return [[key, *value] for key, value in in_dict.items() if value is not None]


def list_br_html_addition(modules_list: list):
    """Replace the newlines ( \n ) by the <br> HTML tag throughout the list.

    Argument:
        :param modules_list     (list) List of lists of compilation results
        :return: updated list - <br> HTML tags added
    """
    for i, sublist in enumerate(modules_list):
        modules_list[i] = [element.replace('\n', '<br>') for element in sublist if isinstance(element, str)]
    return modules_list


def number_that_passed_compilation(in_dict: dict, position: int, compilation_condition: str):
    """
    Return the number of the modules that have compilation status equal to the 'compilation_condition'.

    Arguments:
        :param in_dict                  (dict) Dictionary of key=yang-model, value=list of compilation results
        :param position                 (int) Position in the list where the 'compilation_condidtion' is
        :param compilation_condition    (str) Compilation result we are looking for -
                                              PASSED, PASSED WITH WARNINGS, FAILED
    :return: the number of YANG models which meet the 'compilation_condition'
    """
    total = 0
    for results in in_dict.values():
        if results[position] == compilation_condition:
            total += 1
    return total


def namespace_to_organization(namespace: str) -> str:
    for ns, org in NAMESPACE_MAP:
        if ns in namespace:
            return org
    if 'cisco' in namespace:
        return 'cisco'
    elif 'ietf' in namespace:
        return 'ietf'
    elif 'urn:' in namespace:
        return namespace.split('urn:')[1].split(':')[0]
    return 'independent'


def check_yangcatalog_data(
    config: configparser.ConfigParser,
    yang_file_pseudo_path: str,
    new_module_data: dict,
    compilation_results: dict,
    all_modules: t.Dict[str, dict],
    ietf_type: t.Optional[IETF] = None,
):
    result_html_dir = config.get('Web-Section', 'result-html-dir')
    domain_prefix = config.get('Web-Section', 'domain-prefix')
    save_file_dir = config.get('Directory-Section', 'save-file-dir')
    versions = ValidatorsVersions().get_versions()

    global module_db, incomplete_db
    if not (module_db and incomplete_db):
        module_db = RedisConnection()
        incomplete_db = RedisConnection(modules_db=5)

    yang_file_path = _path_in_dir(yang_file_pseudo_path)
    is_rfc = ietf_type == IETF.RFC
    try:
        parsed_yang = yang_parser.parse(yang_file_path)
    except yang_parser.ParseException:
        print(f'Problem with parsing of: {yang_file_path}')
        return
    name = parsed_yang.arg
    if not name:
        return
    revision = _resolve_revision(parsed_yang)
    name_revision = f'{name}@{revision}'
    if name_revision in all_modules:
        module_data = all_modules[name_revision].copy()
        incomplete = False
        update = False
    else:
        print(f'WARN: {name_revision} not in Redis yet')
        organization = _resolve_organization(parsed_yang, save_file_dir)
        module_data: t.Dict[str, t.Any] = {'name': name, 'revision': revision, 'organization': organization}
        incomplete = True
        update = True
    for field in ('document-name', 'reference', 'author-email'):
        if new_module_data.get(field) and module_data.get(field) != new_module_data[field]:
            update = True
            module_data[field] = new_module_data[field]

    compilation_status = new_module_data.get('compilation-status')
    if compilation_status and module_data.get('compilation-status') != (
        comp_status := compilation_status.lower().replace(' ', '-')
    ):
        # Module parsed with --ietf flag (= RFC) has higher priority
        if is_rfc and ietf_type is None:
            pass
        else:
            update = True
            module_data['compilation-status'] = comp_status

    if compilation_status is not None:
        file_url = _generate_compilation_result_file(
            module_data,
            compilation_results,
            result_html_dir,
            is_rfc,
            versions,
            ietf_type,
        )
        if module_data.get('compilation-status') == 'unknown':
            comp_result = ''
        else:
            comp_result = f'{domain_prefix}/results/{file_url}'
        if module_data.get('compilation-result') != comp_result:
            update = True
            module_data['compilation-result'] = comp_result

    if ietf_type is not None and 'document-name' in new_module_data:
        wg = _resolve_working_group(name_revision, ietf_type, new_module_data['document-name'])
        if (module_data.get('ietf') is None or module_data['ietf']['ietf-wg'] != wg) and wg is not None:
            update = True
            module_data['ietf'] = {}
            module_data['ietf']['ietf-wg'] = wg

    mat_level = _resolve_maturity_level(ietf_type, new_module_data.get('document-name'))
    if module_data.get('maturity-level') != mat_level:
        if mat_level == 'not-applicable' and module_data.get('maturity-level'):
            pass
        else:
            update = True
            module_data['maturity-level'] = mat_level

    if update:
        if incomplete:
            incomplete_db.populate_module(module_data)
        else:
            module_db.populate_module(module_data)
        print(f'DEBUG: updated_modules: {name_revision}')


def _resolve_revision(parsed_yang: Statement) -> str:
    try:
        revision = parsed_yang.search('revision')[0].arg
        if '02-29' in revision:
            revision = revision.replace('02-29', '02-28')
        dateutil.parser.parse(revision)
        year, month, day = map(int, revision.split('-'))
        revision = date(year, month, day).isoformat()
        return revision
    except (IndexError, dateutil.parser.ParserError, ValueError):
        return '1970-01-01'


def _resolve_organization(parsed_yang: Statement, save_file_dir: str) -> str:
    parsed_organization = parsed_yang.search('organization')[0].arg.lower()
    for possible_organization in ORGANIZATIONS:
        if possible_organization in parsed_organization:
            return possible_organization
    if parsed_yang.keyword == 'submodule':
        belongs_to = belongs_to[0].arg if (belongs_to := parsed_yang.search('belongs-to')) else None
        if not belongs_to:
            return 'independent'
        filename = max(glob.glob(os.path.join(save_file_dir, f'{belongs_to}@*.yang')))
        if not filename:
            return 'independent'
        try:
            parsed_yang = yang_parser.parse(os.path.abspath(filename))
        except yang_parser.ParseException:
            return 'independent'
    namespace = namespace[0].arg if (namespace := parsed_yang.search('namespace')) else None
    return namespace_to_organization(namespace) if namespace else 'independent'


def _resolve_maturity_level(ietf_type: t.Optional[IETF], document_name: t.Optional[str]) -> t.Optional[str]:
    if not document_name or not ietf_type:
        return 'not-applicable'
    if ietf_type == IETF.RFC:
        return 'ratified'
    maturity_level = document_name.split('-')[1]
    if 'ietf' in maturity_level:
        return 'adopted'
    return 'initial'


def _resolve_working_group(name_revision: str, ietf_type: IETF, document_name: str):
    if ietf_type == IETF.RFC:
        return IETF_RFC_MAP.get(f'{name_revision}.yang')
    return document_name.split('-')[2]


def _render(tpl_path: str, context: dict) -> str:
    """Render jinja html template
    Arguments:
        :param tpl_path: (str) path to a file
        :param context: (dict) dictionary containing data to render jinja
            template file
        :return: string containing rendered html file
    """
    for key in context['result']:
        context['result'][key] = context['result'][key].replace('\n', '<br>')
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')).get_template(filename).render(context)


def _path_in_dir(yang_file_path: str) -> str:
    yang_path, yang_file = os.path.split(yang_file_path)

    for root, _, files in os.walk(yang_path):
        for ff in files:
            if ff == yang_file:
                return os.path.join(root, ff)
    else:
        print(f'Error: file {yang_file} not found in dir or subdir of {yang_path}')
    return yang_file_path


def _generate_ths(versions: dict, ietf_type: t.Optional[IETF]) -> t.List[str]:
    ths = []
    option = '--lint'
    if ietf_type is not None:
        option = '--ietf'
    pyang_version = versions.get('pyang_version')
    ths.append(f'Compilation Results (pyang {option}). {pyang_version}')
    ths.append(f'Compilation Results (pyang). Note: also generates errors for imported files. {pyang_version}')
    ths.append(
        f'Compilation Results (confdc). Note: '
        f'also generates errors for imported files. {versions.get("confd_version")}',
    )
    ths.append(
        'Compilation Results (yangdump-pro). Note: '
        f'also generates errors for imported files. {versions.get("yangdump_version")}',
    )
    ths.append(
        'Compilation Results (yanglint -i). Note: '
        f'also generates errors for imported files. {versions.get("yanglint_version")}',
    )
    return ths


def _generate_compilation_result_file(
    module_data: dict,
    compilation_results: dict,
    result_html_dir: str,
    is_rfc: bool,
    versions: dict,
    ietf_type: t.Optional[IETF],
) -> str:
    name = module_data['name']
    rev = module_data['revision']
    org = module_data['organization']
    file_url = f'{name}@{rev}_{org}.html'
    compilation_results['name'] = name
    compilation_results['revision'] = rev
    compilation_results['generated'] = time.strftime('%d/%m/%Y')

    context = {'result': compilation_results, 'ths': _generate_ths(versions, ietf_type)}
    template = os.path.dirname(os.path.realpath(__file__)) + '/../resources/compilationStatusTemplate.html'
    rendered_html = _render(template, context)
    result_html_file = os.path.join(result_html_dir, file_url)
    if os.path.isfile(result_html_file):
        with open(result_html_file, 'r', encoding='utf-8') as f:
            existing_output = f.read()
        if existing_output != rendered_html:
            if is_rfc and ietf_type is None:
                pass
            else:
                with open(result_html_file, 'w', encoding='utf-8') as f:
                    f.write(rendered_html)
                os.chmod(result_html_file, 0o664)
    else:
        with open(result_html_file, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        os.chmod(result_html_file, 0o664)

    return file_url
