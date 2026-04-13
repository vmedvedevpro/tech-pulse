from techpulse.pipeline.models import ContentSummary


def format_summary(summary: ContentSummary) -> str:
    score_emoji = "🟢" if summary.relevance_score >= 7 else "🟡" if summary.relevance_score >= 4 else "🔴"
    topics = "\n".join(f"• {t}" for t in summary.key_topics)
    return (
        f"<b>{summary.title}</b>\n\n"
        f"<i>{summary.tldr}</i>\n\n"
        f"<b>Topics:</b>\n{topics}\n\n"
        f"<b>Audience:</b> {summary.target_audience}\n"
        f"<b>Relevance:</b> {score_emoji} {summary.relevance_score}/10 — {summary.relevance_reasoning}"
    )
