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

import abc
import argparse
import datetime
import json
import os
import re
import typing as t
from configparser import ConfigParser
from dataclasses import dataclass

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


class CompileModulesABC(abc.ABC):
    ietf: t.Optional[IETF]
    metadata_generator_cls: t.Type[BaseMetadataGenerator]
    prefix: str
    root_dir: str
    documents_dict: dict
    aggregated_results: dict

    @dataclass
    class Options:
        debug_level: int
        force_compilation: bool
        lint: bool
        allinclusive: bool
        metadata: str
        config: ConfigParser = create_config()

    def __init__(self, options: Options):
        self.config = options.config
        self.yangcatalog_api_prefix = self.config.get('Web-Section', 'yangcatalog-api-prefix')
        self.web_private = self.config.get('Web-Section', 'private-directory') + '/'
        self.cache_directory = self.config.get('Directory-Section', 'cache')
        self.modules_directory = self.config.get('Directory-Section', 'modules-directory')
        self.temp_dir = self.config.get('Directory-Section', 'temp')
        self.ietf_directory = self.config.get('Directory-Section', 'ietf-directory')
        self.cached_compilation_results_path = os.path.join(self.web_private, f'{self.prefix}.json')

        self.debug_level = options.debug_level
        self.lint = options.lint
        self.allinclusive = options.allinclusive
        self.metadata = options.metadata
        self.file_hasher = FileHasher(force_compilation=options.force_compilation, config=self.config)
        self.files_generator = FilesGenerator(self.web_private)
        self.parsers = {
            'pyang': PyangParser(self.debug_level, config=self.config),
            'confdc': ConfdcParser(self.debug_level),
            'yangdumppro': YangdumpProParser(self.debug_level),
            'yanglint': YanglintParser(self.debug_level),
        }
        self.validator_versions = {
            'pyang': validator_versions['pyang_version'],
            'confdc': validator_versions['confd_version'],
            'yangdumppro': validator_versions['yangdump_version'],
            'yanglint': validator_versions['yanglint_version'],
        }

    def __call__(self):
        self._custom_print(f'Start of job in {self.root_dir}')
        self.parser_args = {'root_directory': self.root_dir, 'lint': self.lint, 'allinclusive': self.allinclusive}
        self.yang_list = list_files_by_extensions(
            self.root_dir,
            ('yang',),
            return_full_paths=True,
            recursive=True,
            debug_level=self.debug_level,
        )
        if self.debug_level > 0:
            print(f'yang_list content:\n{self.yang_list}')
        self._custom_print(f'relevant files list built, {len(self.yang_list)} modules found in {self.root_dir}')
        self.modules = self._get_modules()
        self.aggregated_results = self._compile_modules()
        self._custom_print('all modules compiled/validated')
        self._generate_compilation_files()
        compilation_stats = self._generate_statistics_page()
        self._print_compilation_results_summary(compilation_stats)
        self.file_hasher.dump_hashed_files_list()
        self._custom_print(f'end of {os.path.basename(__file__)} job for {self.prefix}')

    def _custom_print(self, message: str):
        timestamp = f'{datetime.datetime.now().time()} ({os.getpid()}):'
        print(f'{timestamp} {message}', flush=True)

    def _get_modules(self) -> dict:
        try:
            with open(os.path.join(self.temp_dir, 'all_modules_data.json'), 'r') as f:
                modules_data = json.load(f)
                self._custom_print('All the modules data loaded from JSON files')
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            modules_data = None
        if not modules_data:
            modules_data = requests.get(f'{self.yangcatalog_api_prefix}/search/modules').json()
            self._custom_print('All the modules data loaded from API')
        modules = {}
        for module in modules_data['module']:
            try:
                modules[f'{module["name"]}@{module["revision"]}'] = module
            except KeyError:
                continue
        return modules

    def _compile_modules(self) -> dict:
        aggregated_results = {'all': {}, 'no_submodules': {}}
        try:
            with open(self.cached_compilation_results_path, 'r') as f:
                cached_compilation_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cached_compilation_results = {}
        for yang_file_path in self.yang_list:
            yang_file_with_revision = self._get_name_with_revision(yang_file_path)
            if not yang_file_with_revision:
                continue
            yang_file_compilation_data = cached_compilation_results.get(yang_file_with_revision)
            previous_compilation_results = (
                yang_file_compilation_data.get('compilation_results')
                if yang_file_compilation_data and isinstance(yang_file_compilation_data, dict)
                else None
            )
            module_hash_info = self.file_hasher.should_parse(yang_file_path)
            changed_validator_versions = module_hash_info.get_changed_validator_versions(self.validator_versions)
            if not previous_compilation_results or module_hash_info.hash_changed or changed_validator_versions:
                parsers_to_use, module_compilation_results = self._get_parsers_to_use_and_previous_compilation_results(
                    previous_compilation_results,
                    module_hash_info,
                    changed_validator_versions,
                )
                compilation_status, module_compilation_results = self._parse_module(
                    parsers_to_use,
                    yang_file_path,
                    **self.parser_args,
                    previous_compilation_results=module_compilation_results,
                )
                metadata_generator = self.metadata_generator_cls(
                    module_compilation_results,
                    compilation_status,
                    yang_file_path,
                    self.documents_dict,
                )
                confd_metadata = metadata_generator.get_confd_metadata()
                yang_file_compilation_data = metadata_generator.get_file_compilation()
                check_yangcatalog_data(
                    self.config,
                    yang_file_path,
                    confd_metadata,
                    module_compilation_results,
                    self.modules,
                    self.ietf,
                )
                # Revert to previous hash if compilation status is 'UNKNOWN' -> try to parse model again next time
                if compilation_status != 'UNKNOWN':
                    self.file_hasher.updated_hashes[yang_file_path] = {
                        'hash': module_hash_info.hash,
                        'validator_versions': self.validator_versions,
                    }
            aggregated_results['all'][yang_file_with_revision] = yang_file_compilation_data
            if module_or_submodule(yang_file_path) == 'module':
                aggregated_results['no_submodules'][yang_file_with_revision] = yang_file_compilation_data
        return aggregated_results

    def _get_name_with_revision(self, yang_file: str) -> str:
        yang_file_base = os.path.basename(yang_file)
        out = self._get_mod_rev(yang_file)
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
                if self.debug_level > 0:
                    print(
                        f'DEBUG: Adding the revision to YANG module because xym can\'t get revision '
                        f'(missing from the YANG module): {yang_file}',
                    )
                    print(f'DEBUG:  out: {new_yang_file_base_with_revision}')
                return new_yang_file_base_with_revision
        print(f'Unable to get name@revision out of {yang_file} - no output', flush=True)
        return ''

    def _get_mod_rev(self, yang_file) -> str:
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

    def _get_parsers_to_use_and_previous_compilation_results(
        self,
        previous_compilation_results: dict,
        module_hash_info: FileHasher.ModuleHashCheckForParsing,
        changed_validator_versions: list[str],
    ) -> tuple[dict, dict]:
        if previous_compilation_results and not module_hash_info.hash_changed and changed_validator_versions:
            parsers_to_use = {
                parser_name: parser_object
                for parser_name, parser_object in self.parsers.items()
                if parser_name in changed_validator_versions
            }
            return parsers_to_use, previous_compilation_results
        return self.parsers, {}

    def _parse_module(
        self,
        parsers: dict,
        yang_file: str,
        root_directory: str,
        lint: bool,
        allinclusive: bool,
        previous_compilation_results: t.Optional[dict] = None,
    ) -> tuple[str, dict]:
        module_compilation_results = previous_compilation_results or {}
        if pyang_parser := parsers.get('pyang'):
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
        if confd_parser := parsers.get('confdc'):
            module_compilation_results['confdrc'] = confd_parser.run_confdc(yang_file, root_directory, allinclusive)
        if yuma_parser := parsers.get('yangdumppro'):
            module_compilation_results['yumadump'] = yuma_parser.run_yumadumppro(
                yang_file,
                root_directory,
                allinclusive,
            )
        if yanglint_parser := parsers.get('yanglint'):
            module_compilation_results['yanglint'] = yanglint_parser.run_yanglint(
                yang_file,
                root_directory,
                allinclusive,
            )
        compilation_status = combined_compilation(os.path.basename(yang_file), module_compilation_results)
        return compilation_status, module_compilation_results

    def _generate_compilation_files(self):
        self.files_generator.write_dictionary(self.aggregated_results['all'], self.prefix)
        headers = self.files_generator.get_yang_page_compilation_headers(self.lint)
        self.files_generator.generate_yang_page_compilation_html(
            self.aggregated_results['no_submodules'],
            headers,
            self.prefix,
            self.metadata,
        )

    def _generate_statistics_page(self) -> dict:
        passed = number_that_passed_compilation(self.aggregated_results['all'], 0, 'PASSED')
        passed_with_warnings = number_that_passed_compilation(self.aggregated_results['all'], 0, 'PASSED WITH WARNINGS')
        total_number = len(self.yang_list)
        failed = total_number - passed - passed_with_warnings
        compilation_stats = {
            'passed': passed,
            'warnings': passed_with_warnings,
            'total': total_number,
            'failed': failed,
        }
        self._write_page_main(self.prefix, compilation_stats)
        self.files_generator.generate_yang_page_main_html(self.prefix, compilation_stats)
        return compilation_stats

    def _write_page_main(self, prefix: str, compilation_stats: dict) -> dict:  # pyright: ignore
        stats_directory = os.path.join(self.web_private, 'stats')
        os.makedirs(stats_directory, exist_ok=True)
        with FileLock(os.path.join(stats_directory, 'stats.json.lock')):
            stats_file_path = os.path.join(stats_directory, 'AllYANGPageMain.json')
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

    def _print_compilation_results_summary(self, compilation_stats: dict):
        print(f'Number of YANG data models from {self.prefix}: {compilation_stats["total"]}')
        print(
            f'Number of YANG data models from {self.prefix} that passed compilation: '
            f'{compilation_stats["passed"]}/{compilation_stats["total"]}',
        )
        print(
            f'Number of YANG data models from {self.prefix} that passed compilation with warnings: '
            f'{compilation_stats["warnings"]}/{compilation_stats["total"]}',
        )
        print(
            f'Number of YANG data models from {self.prefix} that failed compilation: '
            f'{compilation_stats["failed"]}/{compilation_stats["total"]}',
        )


class CompileBaseModules(CompileModulesABC):
    ietf = None
    metadata_generator_cls = BaseMetadataGenerator

    def __init__(self, prefix: str, root_dir: str, options: CompileModulesABC.Options):
        self.prefix = prefix
        super().__init__(options)
        self.root_dir = root_dir
        self.documents_dict = {}


class CompileRfcModules(CompileModulesABC):
    ietf = IETF.RFC
    metadata_generator_cls = RfcMetadataGenerator
    prefix = 'RFCStandard'

    def __init__(self, options: CompileModulesABC.Options):
        super().__init__(options)
        self.root_dir = os.path.join(self.ietf_directory, 'YANG-rfc')
        with open(os.path.join(self.cache_directory, 'rfc_dict.json')) as f:
            self.documents_dict = json.load(f)

    def _generate_compilation_files(self):
        # Create yang module reference table
        module_to_rfc_anchor = {}
        for yang_module, document_name in self.documents_dict.items():
            rfc_name = document_name.split('.')[0]
            datatracker_url = f'https://datatracker.ietf.org/doc/html/{rfc_name}'
            rfc_url_anchor = f'<a href="{datatracker_url}">{rfc_name}</a>'
            module_to_rfc_anchor[yang_module] = rfc_url_anchor
        self.files_generator.write_dictionary(module_to_rfc_anchor, 'IETFYANGRFC')
        headers = ['YANG Model (and submodel)', 'RFC']
        self.files_generator.generate_html_table(module_to_rfc_anchor, headers)
        super()._generate_compilation_files()


class CompileDraftModules(CompileModulesABC):
    ietf = IETF.DRAFT
    metadata_generator_cls = DraftMetadataGenerator
    prefix = 'IETFDraft'
    compilation_status_position = 3

    def __init__(self, options: CompileModulesABC.Options):
        super().__init__(options)
        self.root_dir = os.path.join(self.ietf_directory, 'YANG')
        with open(os.path.join(self.cache_directory, 'draft_dict.json')) as f:
            self.documents_dict = json.load(f)
        self.cached_compilation_results_path = os.path.join(self.web_private, 'IETFCiscoAuthors.json')

    def _generate_compilation_files(self):
        # Generate json and html files with compilation results of modules extracted from IETF Drafts with Cisco authors
        self.files_generator.write_dictionary(self.aggregated_results['all'], 'IETFCiscoAuthors')
        headers = self.files_generator.get_ietf_cisco_authors_yang_page_compilation_headers()
        self.files_generator.generate_yang_page_compilation_html(
            self.aggregated_results['all'],
            headers,
            'IETFCiscoAuthors',
        )
        # Update draft archive cache
        path = os.path.join(self.web_private, 'IETFDraftArchive.json')
        try:
            with open(path) as f:
                old_draft_archive_results = json.load(f)
        except FileNotFoundError:
            old_draft_archive_results = {}
        draft_archive_results = old_draft_archive_results | self.aggregated_results['all']
        self.files_generator.write_dictionary(draft_archive_results, 'IETFDraftArchive')
        # Strip cisco authors out
        for module_data in self.aggregated_results['all'].values():
            compilation_metadata = module_data['compilation_metadata']
            module_data['compilation_metadata'] = compilation_metadata[:2] + compilation_metadata[3:]
        # Generate json and html files with compilation results of modules extracted from IETF Drafts
        self.files_generator.write_dictionary(self.aggregated_results['all'], self.prefix)
        headers = self.files_generator.get_ietf_draft_yang_page_compilation_headers()
        self.files_generator.generate_yang_page_compilation_html(self.aggregated_results['all'], headers, self.prefix)

    def _generate_statistics_page(self) -> dict:
        all_yang_path = os.path.join(self.ietf_directory, 'YANG-all')
        compilation_stats = {
            'total-drafts': len(self.documents_dict),
            'draft-passed': number_that_passed_compilation(
                self.aggregated_results['all'],
                self.compilation_status_position,
                'PASSED',
            ),
            'draft-warnings': number_that_passed_compilation(
                self.aggregated_results['all'],
                self.compilation_status_position,
                'PASSED WITH WARNINGS',
            ),
            'all-ietf-drafts': len(
                [f for f in os.listdir(all_yang_path) if os.path.isfile(os.path.join(all_yang_path, f))],
            ),
        }
        merged_stats = self._write_page_main('ietf-yang', compilation_stats)
        self.files_generator.generate_ietfyang_page_main_html(merged_stats)
        return compilation_stats

    def _print_compilation_results_summary(self, compilation_stats: dict):
        print(f'Number of correctly extracted YANG models from IETF drafts: {compilation_stats["total-drafts"]}')
        print(
            'Number of YANG models in IETF drafts that passed compilation: '
            f'{compilation_stats["draft-passed"]}/{compilation_stats.get("total-drafts")}',
        )
        print(
            'Number of YANG models in IETF drafts that passed compilation with warnings: '
            f'{compilation_stats["draft-warnings"]}/{compilation_stats.get("total-drafts")}',
        )
        print(
            'Number of all YANG models in IETF drafts (examples, badly formatted, etc. ): '
            f'{compilation_stats["all-ietf-drafts"]}',
        )


class CompileDraftArchiveModules(CompileDraftModules):
    ietf = IETF.DRAFT_ARCHIVE
    metadata_generator_cls = ArchivedMetadataGenerator
    prefix = 'IETFDraftArchive'
    compilation_status_position = 4

    def _generate_compilation_files(self):
        self.files_generator.write_dictionary(self.aggregated_results['all'], self.prefix)
        path = os.path.join(self.web_private, 'IETFCiscoAuthors.json')
        try:
            with open(path) as f:
                old_draft_results = json.load(f)
        except FileNotFoundError:
            old_draft_results = {}
        draft_results = old_draft_results | self.aggregated_results['all']
        self.files_generator.write_dictionary(draft_results, 'IETFCiscoAuthors')


class CompileExampleModules(CompileModulesABC):
    ietf = IETF.EXAMPLE
    metadata_generator_cls = ExampleMetadataGenerator
    prefix = 'IETFDraftExample'

    def __init__(self, options: CompileModulesABC.Options):
        super().__init__(options)
        self.root_dir = os.path.join(self.ietf_directory, 'YANG-example')
        with open(os.path.join(self.cache_directory, 'example_dict.json')) as f:
            self.documents_dict = json.load(f)

    def _parse_module(
        self,
        parsers: dict,
        yang_file: str,
        root_directory: str,
        lint: bool,
        allinclusive: bool,
        previous_compilation_results: t.Optional[dict] = None,
    ) -> tuple[str, dict]:
        module_compilation_results = previous_compilation_results or {}
        if pyang_parser := parsers.get('pyang'):
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

    def _generate_compilation_files(self):
        self.files_generator.write_dictionary(self.aggregated_results['all'], self.prefix)
        headers = self.files_generator.get_ietf_draft_example_yang_page_compilation_headers()
        self.files_generator.generate_yang_page_compilation_html(
            self.aggregated_results['no_submodules'],
            headers,
            self.prefix,
        )

    def _generate_statistics_page(self) -> dict:
        compilation_stats = {'example-drafts': len(self.documents_dict)}
        merged_stats = self._write_page_main('ietf-yang', compilation_stats)
        self.files_generator.generate_ietfyang_page_main_html(merged_stats)
        return compilation_stats

    def _print_compilation_results_summary(self, compilation_stats: dict):
        print(
            'Number of correctly extracted example YANG models from IETF drafts: '
            f'{compilation_stats["example-drafts"]}',
            flush=True,
        )


def main():
    config = create_config()
    modules_directory = config.get('Directory-Section', 'modules-directory')
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
        help='Optional flag that determines whether the root_dir directory '
        'contains all imported YANG modules; '
        'If set, the YANG validators will only look in the root_dir directory. '
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
    options = CompileModulesABC.Options(
        debug_level=args.debug,
        force_compilation=args.forcecompilation,
        lint=args.lint,
        allinclusive=args.allinclusive,
        metadata=args.metadata,
        config=config,
    )
    if args.rfc:
        compile_modules_script = CompileRfcModules(options)
    elif args.draft:
        compile_modules_script = CompileDraftModules(options)
    elif args.draft_archive:
        compile_modules_script = CompileDraftArchiveModules(options)
    elif args.example:
        compile_modules_script = CompileExampleModules(options)
    else:
        compile_modules_script = CompileBaseModules(args.prefix, args.rootdir, options)
    compile_modules_script()


if __name__ == '__main__':
    main()
