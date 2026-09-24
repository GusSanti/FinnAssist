import unittest

from scripts.ingest_knowledge import split_markdown


class KnowledgeIngestionTests(unittest.TestCase):
    def test_splits_markdown_by_section_and_repeats_document_title(self):
        chunks = split_markdown(
            "# Reserva de emergência\n\n## Finalidade\n\nPrimeiro texto.\n\n"
            "## Onde guardar\n\nSegundo texto.\n"
        )

        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("# Reserva de emergência\n\n## Finalidade"))
        self.assertTrue(chunks[1].startswith("# Reserva de emergência\n\n## Onde guardar"))


if __name__ == "__main__":
    unittest.main()
