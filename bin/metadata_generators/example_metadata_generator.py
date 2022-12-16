from metadata_generators.draft_metadata_generator import DraftMetadataGenerator


class ExampleMetadataGenerator(DraftMetadataGenerator):
    def get_confd_metadata(self) -> dict:
        return {}

    def get_file_compilation(self) -> DraftMetadataGenerator.FileCompilationData:
        return self.FileCompilationData(
            compilation_metadata=(
                self.draft_url_anchor,
                self.email_anchor,
                self.compilation_status,
            ),
            compilation_results=self.compilation_results.copy(),
        )
