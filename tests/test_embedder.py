import pytest
from unittest.mock import patch, MagicMock


def test_embed_texts_returns_list():
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    with patch("api.services.embedder.get_embedder", return_value=mock_model):
        from api.services.embedder import embed_texts
        result = embed_texts(["hello", "world"])
    assert isinstance(result, list)
    assert len(result) == 2
