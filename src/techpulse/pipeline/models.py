from pydantic import BaseModel, Field


class ContentSummary(BaseModel):
    source_id: str = Field(description="Video ID or content identifier")
    title: str = Field(description="Title of the content")
    source_type: str = Field(description="Source type: youtube, rss, or github")
    tldr: str = Field(description="2-3 sentence summary of the content")
    key_topics: list[str] = Field(description="List of key topics covered")
    target_audience: str = Field(description="Who this content is for")
    relevance_score: int = Field(description="Relevance score 0-10 for tech professionals", ge=0, le=10)
    relevance_reasoning: str = Field(description="Explanation of the relevance score")
    language: str = Field(description="Language code of the content (e.g. 'en', 'ru')")
