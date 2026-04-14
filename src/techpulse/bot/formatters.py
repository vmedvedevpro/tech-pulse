from techpulse.pipeline.models import ContentSummary


def format_summary(summary: ContentSummary) -> str:
    score_emoji = "🟢" if summary.relevance_score >= 7 else "🟡" if summary.relevance_score >= 4 else "🔴"
    topics = "\n".join(f"• {t}" for t in summary.key_topics)
    return (
        f"*{summary.title}*\n\n"
        f"_{summary.tldr}_\n\n"
        f"*Topics:*\n{topics}\n\n"
        f"*Audience:* {summary.target_audience}\n"
        f"*Relevance:* {score_emoji} {summary.relevance_score}/10 — {summary.relevance_reasoning}"
    )
