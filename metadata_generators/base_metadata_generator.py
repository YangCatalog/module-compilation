import os
import typing as t


class BaseMetadataGenerator:
    def __init__(self, compilation_results: dict, compilation_status: str, yang_file: str, document_dict: dict):
        self.compilation_results = compilation_results
        self.compilation_status = compilation_status
        self.yang_file_path = yang_file
        self.yang_file_name = os.path.basename(yang_file)
        self.document_dict = document_dict

    def get_confd_metadata(self) -> dict:
        return {'compilation-status': self.compilation_status}

    class FileCompilationData(t.TypedDict):
        yang_file_path: str
        compilation_metadata: tuple[str, ...]
        compilation_results: dict[str, str]

    def get_file_compilation(self) -> FileCompilationData:
        return self.FileCompilationData(
            yang_file_path=self.yang_file_path,
            compilation_metadata=(self.compilation_status,),
            compilation_results=self.compilation_results.copy(),
        )
