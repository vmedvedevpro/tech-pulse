import argparse

from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from youtube_transcript_api import YouTubeTranscriptApi

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.agent.tools.youtube_transcript_tools import ListTranscriptsTool, YoutubeTranscriptTool
from techpulse.pipeline.integrations.youtube.youtube_api_client import YouTubeTranscriptClient

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Show tool calls and results")
    args = parser.parse_args()

    registry = ToolRegistry()
    yt_client = YouTubeTranscriptClient(YouTubeTranscriptApi())
    registry.register(ListTranscriptsTool(yt_client))
    registry.register(YoutubeTranscriptTool(yt_client))

    agent = Agent(registry, verbose=args.verbose)


    console.print(Panel(Align.center("\n[bold green]TechPulse Agent[/bold green]\n"), subtitle="type q to quit"))
    console.print()

    while True:
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        console.print()

        if user_input.strip().lower() == "q":
            break

        response = agent.chat(user_input)
        console.print(f"[bold green]Agent:[/bold green] ", end="")
        console.print(Markdown(response))
        console.print()


if __name__ == "__main__":
    main()
