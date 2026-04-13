# tech-pulse

![CI](https://github.com/vmedvedevpro/tech-pulse/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/vmedvedevpro/tech-pulse/branch/main/graph/badge.svg)](https://codecov.io/gh/vmedvedevpro/tech-pulse)

Self-hosted tech digest pipeline. YouTube, RSS & GitHub curated by Claude, delivered to Telegram.

TechPulse analyzes YouTube videos using Claude: fetches the transcript, scores relevance for engineers, and produces a
structured summary.

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` environment variable

## Installation

```bash
pip install -e .
```

## Configuration

Copy the example env file and fill in your API key:

```bash
cp .env.example .env
```

| Variable            | Description                                         |
|---------------------|-----------------------------------------------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required)                   |
| `ANTHROPIC_MODEL`   | Model to use (default: `claude-haiku-4-5-20251001`) |

## Usage

```bash
techpulse -l <youtube-url-or-video-id>
```

| Flag              | Description                          |
|-------------------|--------------------------------------|
| `-l`, `--link`    | YouTube URL or video ID (required)   |
| `-v`, `--verbose` | Print tool calls and agent responses |

Examples:

```bash
techpulse -l https://www.youtube.com/watch?v=dQw4w9WgXcQ
techpulse -v -l dQw4w9WgXcQ
```
