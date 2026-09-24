import unittest
from unittest.mock import patch

from app.services.knowledge_service import (
    EMBEDDING_DIMENSIONS,
    _vector_literal,
    create_embeddings,
)


class KnowledgeServiceTests(unittest.TestCase):
    @patch("app.services.knowledge_service.embed")
    def test_creates_768_dimension_embeddings(self, mock_embed):
        mock_embed.return_value = {"embeddings": [[0.1] * EMBEDDING_DIMENSIONS]}

        result = create_embeddings("Tesouro Selic")

        self.assertEqual(len(result[0]), 768)
        mock_embed.assert_called_once_with(
            model="embeddinggemma",
            input=["Tesouro Selic"],
        )

    @patch("app.services.knowledge_service.embed")
    def test_rejects_embedding_with_wrong_dimensions(self, mock_embed):
        mock_embed.return_value = {"embeddings": [[0.1] * 10]}

        with self.assertRaisesRegex(RuntimeError, "esperadas 768"):
            create_embeddings("Reserva")

    def test_vector_literal_validates_dimensions(self):
        with self.assertRaisesRegex(ValueError, "768 dimensions"):
            _vector_literal([0.1])


if __name__ == "__main__":
    unittest.main()
