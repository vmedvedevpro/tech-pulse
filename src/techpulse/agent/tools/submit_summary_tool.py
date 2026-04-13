from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.pipeline.models import ContentSummary


class SubmitSummaryTool(Tool):
    name = "submit_summary"
    description = (
        "Submit the final structured analysis of the content. "
        "Call this as the last step after fetching metadata and transcript. "
        "Fill in all fields carefully and accurately."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "description": "YouTube video ID."},
            "title": {"type": "string", "description": "Title of the video."},
            "source_type": {"type": "string", "description": "Use 'youtube'."},
            "tldr": {"type": "string", "description": "2-3 sentence summary of the content."},
            "key_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key topics covered (5-10 items).",
            },
            "target_audience": {
                "type": "string",
                "description": "Who this content is for (e.g. 'backend engineers').",
            },
            "relevance_score": {
                "type": "integer",
                "description": "Relevance score 0-10 for software engineers.",
            },
            "relevance_reasoning": {
                "type": "string",
                "description": "1-2 sentences explaining the score.",
            },
            "language": {
                "type": "string",
                "description": "Language code of the transcript (e.g. 'en', 'ru').",
            },
        },
        "required": [
            "source_id", "title", "source_type", "tldr", "key_topics",
            "target_audience", "relevance_score", "relevance_reasoning", "language",
        ],
        "additionalProperties": False,
    }

    def __init__(self) -> None:
        self.last_result: ContentSummary | None = None

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        self.last_result = ContentSummary(**tool_input)
        logger.info(
            "submit_summary | source_id={} title={!r} relevance={}/10",
            self.last_result.source_id,
            self.last_result.title,
            self.last_result.relevance_score,
        )
        return ToolResult(content="Summary captured.")
