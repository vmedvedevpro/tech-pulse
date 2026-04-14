import pytest

from techpulse.agent.tools.submit_summary_tool import ContentSummary, SubmitSummaryTool

_VALID_INPUT = {
    "source_id": "abc123",
    "title": "My Video",
    "source_type": "youtube",
    "tldr": "A short summary.",
    "key_topics": ["topic1", "topic2"],
    "target_audience": "backend engineers",
    "relevance_score": 8,
    "relevance_reasoning": "Very relevant to the audience.",
    "language": "en",
}


class TestSubmitSummaryTool:
    @pytest.mark.asyncio
    async def test_run_returns_success_result_when_input_is_valid(self):
        # Arrange
        tool = SubmitSummaryTool()

        # Act
        result = await tool.run(_VALID_INPUT)

        # Assert
        assert not result.is_error
        assert result.content == "Summary captured."

    @pytest.mark.asyncio
    async def test_run_stores_content_summary_when_called(self):
        # Arrange
        tool = SubmitSummaryTool()

        # Act
        await tool.run(_VALID_INPUT)

        # Assert
        assert isinstance(tool.last_result, ContentSummary)
        assert tool.last_result.source_id == "abc123"
        assert tool.last_result.title == "My Video"
        assert tool.last_result.source_type == "youtube"
        assert tool.last_result.relevance_score == 8
        assert tool.last_result.language == "en"

    def test_last_result_is_none_before_first_run(self):
        # Arrange / Act
        tool = SubmitSummaryTool()

        # Assert
        assert tool.last_result is None

    @pytest.mark.asyncio
    async def test_run_overwrites_last_result_when_called_twice(self):
        # Arrange
        tool = SubmitSummaryTool()
        await tool.run(_VALID_INPUT)
        second_input = {**_VALID_INPUT, "source_id": "zzz999", "title": "Another Video"}

        # Act
        await tool.run(second_input)

        # Assert
        assert tool.last_result.source_id == "zzz999"
        assert tool.last_result.title == "Another Video"

    @pytest.mark.asyncio
    async def test_run_raises_when_relevance_score_exceeds_maximum(self):
        # Arrange
        tool = SubmitSummaryTool()
        bad_input = {**_VALID_INPUT, "relevance_score": 11}

        # Act / Assert
        with pytest.raises(Exception):
            await tool.run(bad_input)
