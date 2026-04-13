import argparse
import asyncio

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from techpulse.bootstrap import create_agent
from techpulse.logging import setup_logging
from techpulse.pipeline.models import ContentSummary

console = Console()


def render_summary(summary: ContentSummary) -> None:
    score_color = "green" if summary.relevance_score >= 7 else "yellow" if summary.relevance_score >= 4 else "red"

    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold dim", min_width=18)
    table.add_column()

    table.add_row("Title", summary.title)
    table.add_row("Source", f"[cyan]{summary.source_type}[/cyan]  {summary.source_id}")
    table.add_row("Language", summary.language)
    table.add_row("", "")
    table.add_row("TL;DR", summary.tldr)
    table.add_row("", "")
    table.add_row("Key Topics", "  ".join(f"[dim]•[/dim] {t}" for t in summary.key_topics))
    table.add_row("", "")
    table.add_row("Audience", summary.target_audience)
    table.add_row("", "")
    table.add_row(
        "Relevance",
        f"[{score_color}]{summary.relevance_score}/10[/{score_color}]  {summary.relevance_reasoning}",
    )

    console.print(Panel(table, title="[bold green]ContentSummary[/bold green]", border_style="green"))


async def _run(args) -> None:
    agent, submit_tool = create_agent()
    await agent.chat(args.link)

    if submit_tool.last_result is not None:
        render_summary(submit_tool.last_result)
    else:
        console.print("[yellow]Agent did not submit a summary.[/yellow]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug logs (tool calls, stop reasons)")
    parser.add_argument("-l", "--link", help="YouTube video link or ID to analyze", type=str, required=True)
    args = parser.parse_args()

    setup_logging("DEBUG" if args.verbose else "INFO")

    try:
        asyncio.run(_run(args))
    except Exception as exc:
        logger.error("fatal: {}", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
