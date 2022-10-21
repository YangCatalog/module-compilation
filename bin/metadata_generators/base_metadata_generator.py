import os


class BaseMetadataGenerator:
    def __init__(self, compilation_results: dict, compilation_status: str, yang_file: str, document_dict: dict):
        self.compilation_results = compilation_results
        self.compilation_status = compilation_status
        self.yang_file_name = os.path.basename(yang_file)
        self.document_dict = document_dict

    def get_confd_metadata(self):
        return {'compilation-status': self.compilation_status}

    def get_file_compilation(self):
        return [self.compilation_status, *list(self.compilation_results.values())]
