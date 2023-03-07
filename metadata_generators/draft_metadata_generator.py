import os

from create_config import create_config
from metadata_generators.base_metadata_generator import BaseMetadataGenerator
from metadata_generators.extract_emails import extract_email_string

config = create_config()
ietf_directory = config.get('Directory-Section', 'ietf-directory')


class DraftMetadataGenerator(BaseMetadataGenerator):
    draft_path = config.get('Directory-Section', 'ietf-drafts')
    web_url = config.get('Web-Section', 'my-uri')

    def __init__(self, compilation_results: dict, compilation_status: str, yang_file: str, document_dict: dict):
        super().__init__(compilation_results, compilation_status, yang_file, document_dict)
        self.document_name = self.document_dict[self.yang_file_name]
        draft_name = self.document_name.split('.')[0]
        version_number = draft_name.split('-')[-1]
        self.mailto = '{}@ietf.org'.format(draft_name)
        draft_name = draft_name.rstrip('-0123456789')
        self.datatracker_url = 'https://datatracker.ietf.org/doc/{}/{}'.format(draft_name, version_number)
        self.draft_url_anchor = '<a href="{}">{}</a>'.format(self.datatracker_url, self.document_name)
        self.email_anchor = '<a href="mailto:{}">Email Authors</a>'.format(self.mailto)

    def get_confd_metadata(self) -> dict:
        return {
            'compilation-status': self.compilation_status,
            'reference': self.datatracker_url,
            'document-name': self.document_name,
            'author-email': self.mailto,
        }

    def get_file_compilation(self) -> BaseMetadataGenerator.FileCompilationData:
        draft_file_path = os.path.join(self.draft_path, self.document_dict[self.yang_file_name])
        cisco_email = extract_email_string(draft_file_path, '@cisco.com')
        tailf_email = extract_email_string(draft_file_path, '@tail-f.com')

        draft_emails = ','.join(filter(None, [cisco_email, tailf_email]))
        cisco_email_anchor = '<a href="mailto:{}">Email Cisco Authors Only</a>'.format(draft_emails)
        yang_model_url = '{}/YANG-modules/{}'.format(self.web_url, self.yang_file_name)
        yang_model_anchor = '<a href="{}">Download the YANG model</a>'.format(yang_model_url)
        return self.FileCompilationData(
            yang_file_path=self.yang_file_path,
            compilation_metadata=(
                self.draft_url_anchor,
                self.email_anchor,
                cisco_email_anchor,
                yang_model_anchor,
                self.compilation_status,
            ),
            compilation_results=self.compilation_results.copy(),
        )


class ArchivedMetadataGenerator(DraftMetadataGenerator):
    draft_path = os.path.join(ietf_directory, 'my-id-archive-mirror')
