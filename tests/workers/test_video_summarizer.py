from unittest.mock import AsyncMock, MagicMock

import anthropic
import httpx
import pytest

from techpulse.workers.video_summarizer import VideoSummarizer


def _fake_message(text: str) -> MagicMock:
    block = MagicMock(spec=anthropic.types.TextBlock)
    block.text = text
    message = MagicMock()
    message.content = [block]
    return message


def _make_summarizer(
        *,
        cached_summary: str | None = None,
        generated_text: str = "Generated summary.",
        api_error: bool = False,
        embedding_error: bool = False,
        embedding_vector: list[float] | None = None,
) -> tuple[VideoSummarizer, AsyncMock, AsyncMock, AsyncMock]:
    video_repo = AsyncMock()
    video_repo.get_summary.return_value = cached_summary
    video_repo.set_summary = AsyncMock()
    video_repo.set_summary_embedding = AsyncMock()

    client = AsyncMock()
    if api_error:
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        client.messages.create.side_effect = anthropic.APIError(
            "boom", request=request, body=None
        )
    else:
        client.messages.create.return_value = _fake_message(generated_text)

    embedding_client = AsyncMock()
    if embedding_error:
        embedding_client.embed.side_effect = RuntimeError("voyage down")
    else:
        embedding_client.embed.return_value = embedding_vector or [0.1, 0.2, 0.3]

    summarizer = VideoSummarizer(
        client=client,
        model="claude-haiku-4-5-20251001",
        video_repo=video_repo,
        embedding_client=embedding_client,
    )
    return summarizer, video_repo, client, embedding_client


class TestGetOrCreate:
    @pytest.mark.asyncio
    async def test_returns_cached_summary_without_api_call(self):
        summarizer, video_repo, client, embedding_client = _make_summarizer(
            cached_summary="Old cached."
        )

        result = await summarizer.get_or_create("v1", "transcript", "en")

        assert result == "Old cached."
        client.messages.create.assert_not_called()
        video_repo.set_summary.assert_not_called()
        embedding_client.embed.assert_not_called()
        video_repo.set_summary_embedding.assert_not_called()

    @pytest.mark.asyncio
    async def test_generates_and_persists_when_no_cache(self):
        summarizer, video_repo, client, _ = _make_summarizer(
            cached_summary=None,
            generated_text="Fresh summary.",
        )

        result = await summarizer.get_or_create("v1", "transcript text", "en")

        assert result == "Fresh summary."
        client.messages.create.assert_awaited_once()
        video_repo.set_summary.assert_awaited_once_with("v1", "Fresh summary.")

    @pytest.mark.asyncio
    async def test_passes_language_into_prompt(self):
        summarizer, _, client, _ = _make_summarizer(cached_summary=None)

        await summarizer.get_or_create("v1", "транскрипт", "ru")

        call_kwargs = client.messages.create.await_args.kwargs
        prompt = call_kwargs["messages"][0]["content"]
        assert "ru" in prompt
        assert "транскрипт" in prompt

    @pytest.mark.asyncio
    async def test_uses_configured_model(self):
        summarizer, _, client, _ = _make_summarizer(cached_summary=None)

        await summarizer.get_or_create("v1", "x", "en")

        call_kwargs = client.messages.create.await_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"

    @pytest.mark.asyncio
    async def test_returns_none_and_does_not_persist_on_api_error(self):
        summarizer, video_repo, _, embedding_client = _make_summarizer(
            cached_summary=None, api_error=True
        )

        result = await summarizer.get_or_create("v1", "x", "en")

        assert result is None
        video_repo.set_summary.assert_not_called()
        embedding_client.embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_and_does_not_persist_on_empty_response(self):
        summarizer, video_repo, _, embedding_client = _make_summarizer(
            cached_summary=None, generated_text="   "
        )

        result = await summarizer.get_or_create("v1", "x", "en")

        assert result is None
        video_repo.set_summary.assert_not_called()
        embedding_client.embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_strips_whitespace_from_generated_summary(self):
        summarizer, video_repo, _, _ = _make_summarizer(
            cached_summary=None,
            generated_text="  Summary text.  \n",
        )

        result = await summarizer.get_or_create("v1", "x", "en")

        assert result == "Summary text."
        video_repo.set_summary.assert_awaited_once_with("v1", "Summary text.")


class TestEmbedding:
    @pytest.mark.asyncio
    async def test_embeds_and_persists_after_summary(self):
        summarizer, video_repo, _, embedding_client = _make_summarizer(
            cached_summary=None,
            generated_text="Fresh summary.",
            embedding_vector=[0.4, 0.5, 0.6],
        )

        await summarizer.get_or_create("v1", "transcript", "en")

        embedding_client.embed.assert_awaited_once_with(
            "Fresh summary.", input_type="document"
        )
        video_repo.set_summary_embedding.assert_awaited_once_with(
            "v1", [0.4, 0.5, 0.6]
        )

    @pytest.mark.asyncio
    async def test_summary_persists_even_when_embedding_fails(self):
        summarizer, video_repo, _, embedding_client = _make_summarizer(
            cached_summary=None,
            generated_text="Fresh summary.",
            embedding_error=True,
        )

        result = await summarizer.get_or_create("v1", "transcript", "en")

        assert result == "Fresh summary."
        video_repo.set_summary.assert_awaited_once_with("v1", "Fresh summary.")
        embedding_client.embed.assert_awaited_once()
        video_repo.set_summary_embedding.assert_not_called()
