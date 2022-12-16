from metadata_generators.base_metadata_generator import BaseMetadataGenerator


class RfcMetadataGenerator(BaseMetadataGenerator):
    def get_confd_metadata(self) -> dict:
        document_name = self.document_dict[self.yang_file_name]
        rfc_name = document_name.split('.')[0]
        datatracker_url = 'https://datatracker.ietf.org/doc/html/{}'.format(rfc_name)
        return {
            'compilation-status': self.compilation_status,
            'reference': datatracker_url,
            'document-name': document_name,
            'author-email': None,
        }
