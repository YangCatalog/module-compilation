#!/usr/bin/env python

# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright (c) 2018 Cisco and/or its affiliates.
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

import argparse
import datetime
import json
import os
import re
import typing as t
from configparser import ConfigParser

import requests
from compilation_status import combined_compilation, pyang_compilation_status
from filelock import FileLock

from create_config import create_config
from metadata_generators.base_metadata_generator import BaseMetadataGenerator
from metadata_generators.draft_metadata_generator import ArchivedMetadataGenerator, DraftMetadataGenerator
from metadata_generators.example_metadata_generator import ExampleMetadataGenerator
from metadata_generators.rfc_metadata_generator import RfcMetadataGenerator
from modules_compilation.file_hasher import FileHasher
from modules_compilation.files_generator import FilesGenerator
from parsers.confdc_parser import ConfdcParser
from parsers.pyang_parser import PyangParser
from parsers.yangdump_pro_parser import YangdumpProParser
from parsers.yanglint_parser import YanglintParser
from utility.utility import (
    IETF,
    check_yangcatalog_data,
    list_files_by_extensions,
    module_or_submodule,
    number_that_passed_compilation,
)
from versions import validator_versions

file_basename = os.path.basename(__file__)

__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com'


def get_mod_rev(yang_file) -> str:
    name = ''
    revision = ''

    with open(yang_file, 'r', encoding='utf-8', errors='ignore') as module:
        for line in module:
            if name and revision:
                return f'{name}@{revision}'

            if name == '':
                match = re.search(r'^\s*(sub)?module\s+([\w\-\d]+)', line)
                if match:
                    name = match.group(2).strip()
                    continue

            if not revision:
                match = re.search(r'^\s*revision\s+"?([\d\-]+)"?', line)
                if match:
                    revision = match.group(1).strip()
                    continue

    return f'{name}@{revision}' if revision else name


def custom_print(message: str):
    timestamp = f'{datetime.datetime.now().time()} ({os.getpid()}):'
    print(f'{timestamp} {message}', flush=True)


def get_name_with_revision(yang_file: str) -> str:
    yang_file_base = os.path.basename(yang_file)
    out = get_mod_rev(yang_file)

    if out.rstrip():
        # Add the @revision to the yang_file if not present
        if '@' in yang_file and '.yang' in yang_file:
            new_yang_file_base_with_revision = f'{out.rstrip()}.yang'
            if new_yang_file_base_with_revision.split('@')[0] != yang_file_base.split('@')[0]:
                print(
                    f'Name of the YANG file {yang_file_base} is wrong changing to correct one into '
                    f'{new_yang_file_base_with_revision}',
                    flush=True,
                )
                yang_file_base = new_yang_file_base_with_revision
            if (
                new_yang_file_base_with_revision.split('@')[1].split('.')[0]
                != yang_file_base.split('@')[1].split('.')[0]
            ):
                print(
                    f'Revision of the YANG file {yang_file_base} is wrong changing to correct as '
                    f'{new_yang_file_base_with_revision}',
                    flush=True,
                )
                yang_file_base = new_yang_file_base_with_revision

            return yang_file_base
        else:
            new_yang_file_base_with_revision = f'{out.rstrip()}.yang'
            if debug_level > 0:
                print(
                    f'DEBUG: Adding the revision to YANG module because xym can\'t get revision '
                    f'(missing from the YANG module): {yang_file}',
                )
                print(f'DEBUG:  out: {new_yang_file_base_with_revision}')

            return new_yang_file_base_with_revision
    print(f'Unable to get name@revision out of {yang_file} - no output', flush=True)
    return ''


def get_modules(temp_dir: str, prefix: str) -> dict:
    try:
        with open(os.path.join(temp_dir, 'all_modules_data.json'), 'r') as f:
            modules = json.load(f)
            custom_print('All the modules data loaded from JSON files')
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        modules = {}
    if modules == {}:
        modules = requests.get(f'{prefix}/search/modules').json()
        custom_print('All the modules data loaded from API')
    return modules


def parse_module(
    parsers: dict,
    yang_file: str,
    root_directory: str,
    lint: bool,
    allinclusive: bool,
    previous_compilation_results: t.Optional[dict] = None,
) -> tuple[str, dict]:
    module_compilation_results = previous_compilation_results or {}
    pyang_parser = parsers.get('pyang')
    if pyang_parser:
        module_compilation_results['pyang_lint'] = pyang_parser.run_pyang(
            root_directory,
            yang_file,
            lint,
            allinclusive,
            True,
        )
        module_compilation_results['pyang'] = pyang_parser.run_pyang(
            root_directory,
            yang_file,
            lint,
            allinclusive,
            False,
        )
    confd_parser = parsers.get('confdc')
    if confd_parser:
        module_compilation_results['confdrc'] = confd_parser.run_confdc(yang_file, root_directory, allinclusive)
    yuma_parser = parsers.get('yangdumppro')
    if yuma_parser:
        module_compilation_results['yumadump'] = yuma_parser.run_yumadumppro(yang_file, root_directory, allinclusive)
    yanglint_parser = parsers.get('yanglint')
    if yanglint_parser:
        module_compilation_results['yanglint'] = yanglint_parser.run_yanglint(yang_file, root_directory, allinclusive)
    compilation_status = combined_compilation(os.path.basename(yang_file), module_compilation_results)
    return compilation_status, module_compilation_results


def parse_example_module(
    parsers: dict,
    yang_file: str,
    root_directory: str,
    lint: bool,
    allinclusive: bool,
    previous_compilation_results: t.Optional[dict] = None,
):
    module_compilation_results = previous_compilation_results or {}
    pyang_parser = parsers.get('pyang')
    if pyang_parser:
        module_compilation_results['pyang_lint'] = pyang_parser.run_pyang(
            root_directory,
            yang_file,
            lint,
            allinclusive,
            True,
        )
        module_compilation_results['pyang'] = pyang_parser.run_pyang(
            root_directory,
            yang_file,
            lint,
            allinclusive,
            False,
        )
    compilation_status = pyang_compilation_status(module_compilation_results['pyang_lint'])
    return compilation_status, module_compilation_results


def validate(
    prefix: str,
    modules: dict,
    yang_list: list,
    parser_args: dict,
    document_dict: dict,
    config: ConfigParser,
) -> dict:
    agregate_results = {'all': {}, 'no_submodules': {}}
    parsers = {
        'pyang': PyangParser(debug_level, config=config),
        'confdc': ConfdcParser(debug_level),
        'yangdumppro': YangdumpProParser(debug_level),
        'yanglint': YanglintParser(debug_level),
    }
    all_yang_catalog_metadata = {}
    for module in modules['module']:
        try:
            key = f'{module["name"]}@{module["revision"]}'
        except KeyError:
            continue
        all_yang_catalog_metadata[key] = module

    cached_compilation_results_filename = 'IETFCiscoAuthors.json' if ietf == IETF.DRAFT else f'{prefix}.json'
    cached_compilation_results_path = os.path.join(web_private, cached_compilation_results_filename)
    try:
        with open(cached_compilation_results_path, 'r') as f:
            cached_compilation_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cached_compilation_results = {}

    validator_versions_to_check = {
        'pyang': validator_versions['pyang_version'],
        'confdc': validator_versions['confd_version'],
        'yangdumppro': validator_versions['yangdump_version'],
        'yanglint': validator_versions['yanglint_version'],
    }
    for yang_file_path in yang_list:
        yang_file_with_revision = get_name_with_revision(yang_file_path)
        if not yang_file_with_revision:
            continue
        yang_file_compilation_data = cached_compilation_results.get(yang_file_with_revision)
        previous_compilation_results = (
            yang_file_compilation_data.get('compilation_results')
            if yang_file_compilation_data and isinstance(yang_file_compilation_data, dict)
            else None
        )
        module_hash_info = file_hasher.should_parse(yang_file_path)
        changed_validator_versions = module_hash_info.get_changed_validator_versions(validator_versions_to_check)
        if not previous_compilation_results or module_hash_info.hash_changed or changed_validator_versions:
            parsers_to_use, module_compilation_results = _get_module_parsers_to_use_and_previous_compilation_results(
                parsers,
                previous_compilation_results,
                module_hash_info,
                changed_validator_versions,
            )
            compilation_status, module_compilation_results = _parse_module(
                yang_file_path,
                parsers_to_use,
                parser_args,
                module_compilation_results,
            )

            metadata_generator = metadata_generator_cls(
                module_compilation_results,
                compilation_status,
                yang_file_path,
                document_dict,
            )
            confd_metadata = metadata_generator.get_confd_metadata()
            yang_file_compilation_data = metadata_generator.get_file_compilation()

            check_yangcatalog_data(
                config,
                yang_file_path,
                confd_metadata,
                module_compilation_results,
                all_yang_catalog_metadata,
                ietf,
            )

            # Revert to previous hash if compilation status is 'UNKNOWN' -> try to parse model again next time
            if compilation_status != 'UNKNOWN':
                file_hasher.updated_hashes[yang_file_path] = {
                    'hash': module_hash_info.hash,
                    'validator_versions': validator_versions_to_check,
                }

        agregate_results['all'][yang_file_with_revision] = yang_file_compilation_data
        if module_or_submodule(yang_file_path) == 'module':
            agregate_results['no_submodules'][yang_file_with_revision] = yang_file_compilation_data
    return agregate_results


def _get_module_parsers_to_use_and_previous_compilation_results(
    all_parsers: dict,
    previous_compilation_results: dict,
    module_hash_info: FileHasher.ModuleHashCheckForParsing,
    changed_validator_versions: list[str],
) -> tuple[dict, dict]:
    if previous_compilation_results and not module_hash_info.hash_changed and changed_validator_versions:
        parsers_to_use = {
            parser_name: parser_object
            for parser_name, parser_object in all_parsers.items()
            if parser_name in changed_validator_versions
        }
        return parsers_to_use, previous_compilation_results
    return all_parsers, {}


def _parse_module(
    yang_file_path: str,
    parsers_to_use: dict,
    parser_args: dict,
    previous_compilation_results: dict,
) -> tuple[str, dict]:
    if ietf == IETF.EXAMPLE:
        return parse_example_module(
            parsers_to_use, yang_file_path, **parser_args, previous_compilation_results=previous_compilation_results
        )
    return parse_module(
        parsers_to_use, yang_file_path, **parser_args, previous_compilation_results=previous_compilation_results
    )


def write_page_main(prefix: str, compilation_stats: dict) -> dict:  # pyright: ignore
    stats_directory = os.path.join(web_private, 'stats')
    os.makedirs(stats_directory, exist_ok=True)
    with FileLock(os.path.join(stats_directory, 'stats.json.lock')):
        stats_file_path = os.path.join(stats_directory, 'AllYANGPageMain.json')
        counter = 5
        while True:
            try:
                if not os.path.exists(stats_file_path):
                    with open(stats_file_path, 'w') as writer:
                        writer.write('{}')
                with open(stats_file_path, 'r') as reader:
                    stats = json.load(reader)
                    if stats.get(prefix):
                        stats[prefix].update(compilation_stats)
                    else:
                        stats[prefix] = compilation_stats
                with open(stats_file_path, 'w') as writer:
                    json.dump(stats, writer)
                return stats[prefix]
            # NOTE: what kind of exception is expected here?
            except Exception:
                counter = counter - 1
                if counter == 0:
                    break


def main():
    global config, debug_level, file_hasher, ietf, metadata_generator_cls, web_private
    config = create_config()
    yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
    web_private = config.get('Web-Section', 'private-directory') + '/'
    cache_directory = config.get('Directory-Section', 'cache')
    modules_directory = config.get('Directory-Section', 'modules-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    ietf_directory = config.get('Directory-Section', 'ietf-directory')

    parser = argparse.ArgumentParser(
        description='YANG Document Processor: generate tables with compilation errors/warnings',
    )
    parser.add_argument(
        '--rootdir',
        help='Root directory where to find the source YANG models. Default is "."',
        type=str,
        default='.',
    )
    parser.add_argument(
        '--metadata',
        help='Metadata text (such as SDOs, Github location, etc.) to be displayed on the generated HTML page. '
        'Default is ""',
        type=str,
        default='',
    )
    parser.add_argument(
        '--lint',
        help='Optional flag that determines pyang syntax enforcement; '
        'If set, pyang --lint is run. '
        'Otherwise, pyang --ietf is run. '
        'Default is False',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--allinclusive',
        help='Optional flag that determines whether the rootdir directory '
        'contains all imported YANG modules; '
        'If set, the YANG validators will only look in the rootdir directory. '
        f'Otherwise, the YANG validators look in {modules_directory}. '
        'Default is False',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--prefix',
        help='Prefix for generating HTML file names. Example: MEF, IEEEStandard, IEEEExperimental. Default is ""',
        default='',
    )
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)
    parser.add_argument(
        '--forcecompilation',
        help='Optional flag that determines wheter compilation should be run '
        'for all files even if they have not been changed '
        'or even if the validators versions have not been changed.',
        action='store_true',
        default=False,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--rfc', help='Set specific options for compiling RFCs.', action='store_true')
    group.add_argument(
        '--draft',
        help='Include extra metadata in the compilation results when compiling drafts. '
        'Does not include archived drafts.',
        action='store_true',
    )
    group.add_argument(
        '--draft-archive',
        help='Include extra metadata in the compilation results when compiling drafts. Includes archived drafts.',
        action='store_true',
    )
    group.add_argument(
        '--example',
        help='Include extra metadata in the compilation results when compiling examples,'
        ' only compile examples with pyang.',
        action='store_true',
    )
    args = parser.parse_args()

    # Set options depending on the type of documents we're compiling
    if not any([args.draft, args.draft_archive, args.example, args.rfc]):
        ietf = None
        metadata_generator_cls = BaseMetadataGenerator
        document_dict = {}
    elif args.rfc:
        ietf = IETF.RFC
        metadata_generator_cls = RfcMetadataGenerator
        with open(os.path.join(cache_directory, 'rfc_dict.json')) as f:
            document_dict = json.load(f)
        args.prefix = 'RFCStandard'
        args.rootdir = os.path.join(ietf_directory, 'YANG-rfc')
    elif args.draft or args.draft_archive:
        if args.draft_archive:
            ietf = IETF.DRAFT_ARCHIVE
            metadata_generator_cls = ArchivedMetadataGenerator
            args.prefix = 'IETFDraftArchive'
        else:
            ietf = IETF.DRAFT
            metadata_generator_cls = DraftMetadataGenerator
            args.prefix = 'IETFDraft'
        with open(os.path.join(cache_directory, 'draft_dict.json')) as f:
            document_dict = json.load(f)
        args.rootdir = os.path.join(ietf_directory, 'YANG')
    elif args.example:
        ietf = IETF.EXAMPLE
        metadata_generator_cls = ExampleMetadataGenerator
        with open(os.path.join(cache_directory, 'example_dict.json')) as f:
            document_dict = json.load(f)
        args.prefix = 'IETFDraftExample'
        args.rootdir = os.path.join(ietf_directory, 'YANG-example')
    else:
        raise RuntimeError('Incorrect ietf arg')

    custom_print(f'Start of job in {args.rootdir}')

    debug_level = args.debug

    # Get list of hashed files
    file_hasher = FileHasher(force_compilation=args.forcecompilation, config=config)

    modules = get_modules(temp_dir, yangcatalog_api_prefix)

    yang_list = list_files_by_extensions(
        args.rootdir,
        ('yang',),
        return_full_paths=True,
        recursive=True,
        debug_level=args.debug,
    )

    parser_args = {'root_directory': args.rootdir, 'lint': args.lint, 'allinclusive': args.allinclusive}

    if debug_level > 0:
        print(f'yang_list content:\n{yang_list}')
    custom_print(f'relevant files list built, {len(yang_list)} modules found in {args.rootdir}')
    aggregate_results = validate(args.prefix, modules, yang_list, parser_args, document_dict, config)
    custom_print('all modules compiled/validated')

    # Generate HTML and JSON files
    files_generator = FilesGenerator(web_private)
    if ietf == IETF.DRAFT:
        # Generate json and html files with compilation results of modules extracted from IETF Drafts with Cisco authors
        files_generator.write_dictionary(aggregate_results['all'], 'IETFCiscoAuthors')
        headers = files_generator.get_ietf_cisco_authors_yang_page_compilation_headers()
        files_generator.generate_yang_page_compilation_html(aggregate_results['all'], headers, 'IETFCiscoAuthors')

        # Update draft archive cache
        path = os.path.join(web_private, 'IETFDraftArchive.json')
        try:
            with open(path) as f:
                old_draft_archive_results = json.load(f)
        except FileNotFoundError:
            old_draft_archive_results = {}
        draft_archive_results = old_draft_archive_results | aggregate_results['all']
        files_generator.write_dictionary(draft_archive_results, 'IETFDraftArchive')

        # Strip cisco authors out
        for module_data in aggregate_results['all'].values():
            compilation_metadata = module_data['compilation_metadata']
            module_data['compilation_metadata'] = compilation_metadata[:2] + compilation_metadata[3:]

        # Generate json and html files with compilation results of modules extracted from IETF Drafts
        files_generator.write_dictionary(aggregate_results['all'], args.prefix)
        headers = files_generator.get_ietf_draft_yang_page_compilation_headers()
        files_generator.generate_yang_page_compilation_html(aggregate_results['all'], headers, args.prefix)
    elif ietf == IETF.DRAFT_ARCHIVE:
        files_generator.write_dictionary(aggregate_results['all'], args.prefix)

        # Update draft cache
        path = os.path.join(web_private, 'IETFCiscoAuthors.json')
        try:
            with open(path) as f:
                old_draft_results = json.load(f)
        except FileNotFoundError:
            old_draft_results = {}
        draft_results = old_draft_results | aggregate_results['all']
        files_generator.write_dictionary(draft_results, 'IETFCiscoAuthors')
    elif ietf == IETF.EXAMPLE:
        files_generator.write_dictionary(aggregate_results['all'], args.prefix)
        headers = files_generator.get_ietf_draft_example_yang_page_compilation_headers()
        files_generator.generate_yang_page_compilation_html(aggregate_results['no_submodules'], headers, args.prefix)
    else:
        if ietf == IETF.RFC:
            # Create yang module reference table
            module_to_rfc_anchor = {}
            for yang_module, document_name in document_dict.items():
                rfc_name = document_name.split('.')[0]
                datatracker_url = f'https://datatracker.ietf.org/doc/html/{rfc_name}'
                rfc_url_anchor = f'<a href="{datatracker_url}">{rfc_name}</a>'
                module_to_rfc_anchor[yang_module] = rfc_url_anchor

            files_generator.write_dictionary(module_to_rfc_anchor, 'IETFYANGRFC')
            headers = ['YANG Model (and submodel)', 'RFC']
            files_generator.generate_html_table(module_to_rfc_anchor, headers)

        files_generator.write_dictionary(aggregate_results['all'], args.prefix)
        headers = files_generator.get_yang_page_compilation_headers(args.lint)
        files_generator.generate_yang_page_compilation_html(
            aggregate_results['no_submodules'],
            headers,
            args.prefix,
            args.metadata,
        )

    # Generate modules compilation results statistics HTML page
    if ietf in (IETF.DRAFT, IETF.DRAFT_ARCHIVE):
        all_yang_path = os.path.join(ietf_directory, 'YANG-all')
        compilation_status_position = 3 if ietf == IETF.DRAFT else 4
        compilation_stats = {
            'total-drafts': len(document_dict),
            'draft-passed': number_that_passed_compilation(
                aggregate_results['all'],
                compilation_status_position,
                'PASSED',
            ),
            'draft-warnings': number_that_passed_compilation(
                aggregate_results['all'],
                compilation_status_position,
                'PASSED WITH WARNINGS',
            ),
            'all-ietf-drafts': len(
                [f for f in os.listdir(all_yang_path) if os.path.isfile(os.path.join(all_yang_path, f))],
            ),
        }
        merged_stats = write_page_main('ietf-yang', compilation_stats)
        files_generator.generate_ietfyang_page_main_html(merged_stats)
    elif ietf == IETF.EXAMPLE:
        compilation_stats = {'example-drafts': len(document_dict.keys())}
        merged_stats = write_page_main('ietf-yang', compilation_stats)
        files_generator.generate_ietfyang_page_main_html(merged_stats)
    else:
        passed = number_that_passed_compilation(aggregate_results['all'], 0, 'PASSED')
        passed_with_warnings = number_that_passed_compilation(aggregate_results['all'], 0, 'PASSED WITH WARNINGS')
        total_number = len(yang_list)
        failed = total_number - passed - passed_with_warnings
        compilation_stats = {
            'passed': passed,
            'warnings': passed_with_warnings,
            'total': total_number,
            'failed': failed,
        }
        write_page_main(args.prefix, compilation_stats)
        files_generator.generate_yang_page_main_html(args.prefix, compilation_stats)

    _print_compilation_results_summary(args.prefix, ietf, compilation_stats)
    custom_print(f'end of {os.path.basename(__file__)} job for {args.prefix}')

    # Update files content hashes and dump into .json file
    file_hasher.dump_hashed_files_list()


def _print_compilation_results_summary(files_prefix: str, ietf: IETF, compilation_stats: dict):
    print('--------------------------')
    if ietf in (IETF.DRAFT, IETF.DRAFT_ARCHIVE):
        print(f'Number of correctly extracted YANG models from IETF drafts: {compilation_stats["total-drafts"]}')
        print(
            'Number of YANG models in IETF drafts that passed compilation: '
            f'{compilation_stats["draft-passed"]}/{compilation_stats.get("total-drafts")}',
        )
        print(
            'Number of YANG models in IETF drafts that passed compilation with warnings: '
            f'{compilation_stats["draft-warnings"]}/{compilation_stats.get("total-drafts")}',
        ),
        print(
            'Number of all YANG models in IETF drafts (examples, badly formatted, etc. ): '
            f'{compilation_stats["all-ietf-drafts"]}',
        )
    elif ietf == IETF.EXAMPLE:
        print(
            'Number of correctly extracted example YANG models from IETF drafts: '
            f'{compilation_stats["example-drafts"]}',
            flush=True,
        )
    else:
        print(f'Number of YANG data models from {files_prefix}: {compilation_stats["total"]}')
        print(
            f'Number of YANG data models from {files_prefix} that passed compilation: '
            f'{compilation_stats["passed"]}/{compilation_stats["total"]}',
        )
        print(
            f'Number of YANG data models from {files_prefix} that passed compilation with warnings: '
            f'{compilation_stats["warnings"]}/{compilation_stats["total"]}',
        )
        print(
            f'Number of YANG data models from {files_prefix} that failed compilation: '
            f'{compilation_stats["failed"]}/{compilation_stats["total"]}',
        )


if __name__ == '__main__':
    main()
