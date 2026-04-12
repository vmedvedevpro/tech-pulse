from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry

console = Console()


def main() -> None:
    registry = ToolRegistry()

    agent = Agent(registry)


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
