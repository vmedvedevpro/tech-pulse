from typing import Final

import anthropic
from loguru import logger

from techpulse.embeddings import EmbeddingClient
from techpulse.persistence.repositories.protocols import VideoRepositoryProtocol
from techpulse.workers.video_summarizer_prompt import SUMMARIZE_PROMPT

_MAX_TOKENS: Final = 512


class VideoSummarizer:
    def __init__(
            self,
            client: anthropic.AsyncAnthropic,
            model: str,
            video_repo: VideoRepositoryProtocol,
            embedding_client: EmbeddingClient,
    ) -> None:
        self._client = client
        self._model = model
        self._video_repo = video_repo
        self._embedding_client = embedding_client

    async def get_or_create(
            self,
            video_id: str,
            transcript: str,
            language: str,
    ) -> str | None:
        cached = await self._video_repo.get_summary(video_id)
        if cached is not None:
            logger.debug("summary cache hit | video_id={}", video_id)
            return cached

        summary = await self._generate(transcript, language)
        if summary is None:
            return None

        await self._video_repo.set_summary(video_id, summary)
        logger.info("summary persisted | video_id={} length={}", video_id, len(summary))
        await self._embed_summary(video_id, summary)
        return summary

    async def _embed_summary(self, video_id: str, summary: str) -> None:
        try:
            embedding = await self._embedding_client.embed(summary, input_type="document")
        except Exception as exc:
            logger.warning("embedding generation failed | video_id={} | {}", video_id, exc)
            return
        await self._video_repo.set_summary_embedding(video_id, embedding)
        logger.info("summary embedding persisted | video_id={}", video_id)

    async def _generate(self, transcript: str, language: str) -> str | None:
        prompt = SUMMARIZE_PROMPT.format(language=language, transcript=transcript)
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            logger.warning("summarizer api error | {}", exc)
            return None

        parts = [block.text for block in message.content if isinstance(block, anthropic.types.TextBlock)]
        text = "".join(parts).strip()
        return text or None
