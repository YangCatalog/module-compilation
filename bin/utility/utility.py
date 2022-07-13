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
import json
import os
import time
import typing as t

import jinja2
import requests
from redis_connections.redis_connection import RedisConnection
from versions import ValidatorsVersions

from utility.static_variables import IETF_RFC_MAP


def push_to_redis(updated_modules: list, config: configparser.ConfigParser):
    json_modules_data = json.dumps({'modules': {'module': updated_modules}})
    credentials = config.get('Secrets-Section', 'confd-credentials').strip('"').split()
    confd_prefix = config.get('Web-Section', 'confd-prefix')

    if '{"module": []}' not in json_modules_data:
        print('Creating patch request to ConfD with updated data')
        url = '{}/restconf/data/yang-catalog:catalog/modules/'.format(confd_prefix)
        response = requests.patch(url, data=json_modules_data,
                                  auth=(credentials[0], credentials[1]),
                                  headers={
                                      'Accept': 'application/yang-data+json',
                                      'Content-type': 'application/yang-data+json'})
        if response.status_code < 200 or response.status_code > 299:
            print('Request with body {} on path {} failed with {}'.
                  format(json_modules_data, url, response.text))
        RedisConnection().populate_modules(updated_modules)


def module_or_submodule(yang_file_path: str):
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
        print('File {} is not yang file or not well formated'.format(yang_file_path))
        return 'wrong file'
    else:
        return None


def dict_to_list(in_dict: dict, is_rfc: bool = False):
    """ Create a list out of compilation results from 'in_dict' dictionary variable.
    First element of each list is name of the module, second one is compilation-status 
    which is followed by compilation-results.

    Argument:
        :param in_dict      (dict) Dictionary of modules with compilation results
        :param is_rfc       (bool) Whether we are tranforming dictionary containing RFC modules 
                                    - it has slightly different structure
        :return: List of lists of compilation results
    """
    if is_rfc:
        dict_list = [[key, value] for key, value in in_dict.items() if value is not None]
    else:
        dict_list = [[key, *value] for key, value in in_dict.items() if value is not None]

    return dict_list


def list_br_html_addition(modules_list: list):
    """ Replace the newlines ( \n ) by the <br> HTML tag throughout the list.

    Argument:
        :param modules_list     (list) List of lists of compilation results
        :return: updated list - <br> HTML tags added
    """
    for i, sublist in enumerate(modules_list):
        modules_list[i] = [element.replace('\n', '<br>') for element in sublist if isinstance(element, str)]

    return modules_list


def _resolve_maturity_level(ietf_type: t.Optional[str], document_name: t.Optional[str]):
    if ietf_type == 'ietf-rfc':
        return 'ratified'
    elif ietf_type in ['ietf-draft', 'ietf-example']:
        assert document_name, 'If this is an IETF module, it ought to have a reference document'
        maturity_level = document_name.split('-')[1]
        if 'ietf' in maturity_level:
            return 'adopted'
        else:
            return 'initial'
    else:
        return 'not-applicable'


def _resolve_working_group(name_revision: str, ietf_type: str, document_name: str):
    if ietf_type == 'ietf-rfc':
        return IETF_RFC_MAP.get('{}.yang'.format(name_revision))
    else:
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
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def _path_in_dir(yang_file_path: str) -> str:
    yang_path, yang_file = os.path.split(yang_file_path)

    for root, _, files in os.walk(yang_path):
        for ff in files:
            if ff == yang_file:
                return os.path.join(root, ff)
    else:
        print('Error: file {} not found in dir or subdir of {}'.format(yang_file, yang_path))
    return yang_file_path


def _generate_ths(versions: dict, ietf_type: t.Optional[str]) -> t.List[str]:
    ths = list()
    option = '--lint'
    if ietf_type is not None:
        option = '--ietf'
    ths.append('Compilation Results (pyang {}). {}'.format(option, versions.get('pyang_version')))
    ths.append('Compilation Results (pyang). Note: also generates errors for imported files. {}'.format(
        versions.get('pyang_version')))
    ths.append('Compilation Results (confdc). Note: also generates errors for imported files. {}'.format(
        versions.get('confd_version')))
    ths.append('Compilation Results (yangdump-pro). Note: also generates errors for imported files. {}'.format(
        versions.get('yangdump_version')))
    ths.append(
        'Compilation Results (yanglint -i). Note: also generates errors for imported files. {}'.format(
            versions.get('yanglint_version')))
    return ths


def _generate_compilation_result_file(module_data: dict, compilation_results: dict, result_html_dir: str,
                                      is_rfc: bool, versions: dict, ietf_type: t.Optional[str]) -> str:
    name = module_data['name']
    rev = module_data['revision']
    org = module_data['organization']
    file_url = '{}@{}_{}.html'.format(name, rev, org)
    compilation_results['name'] = name
    compilation_results['revision'] = rev
    compilation_results['generated'] = time.strftime('%d/%m/%Y')

    context = {'result': compilation_results,
               'ths': _generate_ths(versions, ietf_type)}
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


def check_yangcatalog_data(config: configparser.ConfigParser, yang_file_pseudo_path: str, new_module_data: dict,
                           compilation_results: dict, all_modules: t.Dict[str, dict], ietf_type: t.Optional[str] = None):
    pyang_exec = config.get('Tool-Section', 'pyang-exec')
    result_html_dir = config.get('Web-Section', 'result-html-dir')
    domain_prefix = config.get('Web-Section', 'domain-prefix')
    versions = ValidatorsVersions().get_versions()

    yang_file_path = _path_in_dir(yang_file_pseudo_path)
    is_rfc = ietf_type == 'ietf-rfc'

    updated_modules = []
    name_revision_command = 'pypy3 {} -fname --name-print-revision --path="$MODULES" {} 2> /dev/null'.format(pyang_exec, yang_file_path)
    name_revision = os.popen(name_revision_command).read().rstrip().split(' ')[0]
    if '@' not in name_revision:
        name_revision += '@1970-01-01'
    if name_revision in all_modules:
        module_data = all_modules[name_revision].copy()
        update = False

        for field in ['document-name', 'reference', 'author-email']:
            if new_module_data.get(field) and module_data.get(field) != new_module_data[field]:
                update = True
                module_data[field] = new_module_data[field]

        if new_module_data.get('compilation-status') \
                and module_data.get('compilation-status') != new_module_data['compilation-status'].lower().replace(' ', '-'):
            # Module parsed with --ietf flag (= RFC) has higher priority
            if is_rfc and ietf_type is None:
                pass
            else:
                update = True
                module_data['compilation-status'] = new_module_data['compilation-status'].lower().replace(' ', '-')

        if new_module_data.get('compilation-status') is not None:
            file_url = _generate_compilation_result_file(module_data, compilation_results,
                                                         result_html_dir, is_rfc, versions, ietf_type)
            if module_data.get('compilation-status') == 'unknown':
                comp_result = ''
            else:
                comp_result = '{}/results/{}'.format(domain_prefix, file_url)
            if module_data.get('compilation-result') != comp_result:
                update = True
                module_data['compilation-result'] = comp_result

        if ietf_type is not None and module_data.get('organization') == 'ietf' and 'document-name' in new_module_data:
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
            updated_modules.append(module_data)
            print('DEBUG: updated_modules: {}'.format(name_revision))
    else:
        print('WARN: {} not in Redis yet'.format(name_revision))
    return updated_modules


def number_that_passed_compilation(in_dict: dict, position: int, compilation_condition: str):
    """
    Return the number of the modules that have compilation status equal to the 'compilation_condition'.

    Arguments:
        :param in_dict                  (dict) Dictionary of key:yang-model, value:list of compilation results
        :param position                 (int) Position in the list where the 'compilation_condidtion' is
        :param compilation_condition    (str) Compilation result we are looking for - PASSED, PASSED WITH WARNINGS, FAILED
    :return: the number of YANG models which meet the 'compilation_condition'
    """
    total = 0
    for results in in_dict.values():
        if results[position] == compilation_condition:
            total += 1
    return total
