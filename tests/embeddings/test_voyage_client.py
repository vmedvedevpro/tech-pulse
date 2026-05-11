from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from techpulse.embeddings import VoyageEmbeddingClient


def _fake_embeddings(vectors: list[list[float]]) -> MagicMock:
    result = MagicMock()
    result.embeddings = vectors
    return result


def _make_client(vectors: list[list[float]]) -> tuple[VoyageEmbeddingClient, AsyncMock]:
    with patch("techpulse.embeddings.voyage_client.voyageai.AsyncClient") as ctor:
        sdk = MagicMock()
        sdk.embed = AsyncMock(return_value=_fake_embeddings(vectors))
        ctor.return_value = sdk
        client = VoyageEmbeddingClient(api_key="test", model="voyage-3-lite")
    return client, sdk.embed


class TestEmbed:
    @pytest.mark.asyncio
    async def test_returns_single_vector(self):
        client, embed_mock = _make_client([[0.1, 0.2, 0.3]])

        result = await client.embed("hello")

        assert result == [0.1, 0.2, 0.3]
        embed_mock.assert_awaited_once_with(
            ["hello"], model="voyage-3-lite", input_type="document"
        )

    @pytest.mark.asyncio
    async def test_passes_query_input_type(self):
        client, embed_mock = _make_client([[1.0]])

        await client.embed("search this", input_type="query")

        embed_mock.assert_awaited_once_with(
            ["search this"], model="voyage-3-lite", input_type="query"
        )


class TestEmbedBatch:
    @pytest.mark.asyncio
    async def test_returns_all_vectors(self):
        vectors = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        client, embed_mock = _make_client(vectors)

        result = await client.embed_batch(["a", "b", "c"])

        assert result == vectors
        embed_mock.assert_awaited_once_with(
            ["a", "b", "c"], model="voyage-3-lite", input_type="document"
        )

    @pytest.mark.asyncio
    async def test_passes_query_input_type(self):
        client, embed_mock = _make_client([[1.0], [2.0]])

        await client.embed_batch(["q1", "q2"], input_type="query")

        embed_mock.assert_awaited_once_with(
            ["q1", "q2"], model="voyage-3-lite", input_type="query"
        )
