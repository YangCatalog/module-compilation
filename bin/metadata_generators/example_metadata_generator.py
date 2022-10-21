from metadata_generators.draft_metadata_generator import DraftMetadataGenerator


class ExampleMetadataGenerator(DraftMetadataGenerator):
    def get_confd_metadata(self):
        return {}

    def get_file_compilation(self):
        return [
            self.draft_url_anchor,
            self.email_anchor,
            self.compilation_status,
            *list(self.compilation_results.values()),
        ]
