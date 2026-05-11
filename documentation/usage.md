# Usage

Chat with [@aitechpulsebot](https://t.me/aitechpulsebot) using natural language — the agent picks the right tools
based on intent.

## YouTube channels

- `Add channel @nickchapsas`
- `Show my channels`
- `Remove @channel_handle`

## GitHub repositories

- `Track microsoft/vscode`
- `Show my repos`
- `Stop tracking vercel/next.js`
- `What's the latest release of astral-sh/uv?`
- `Tell me about the facebook/react repo`

## Interest topics

- `Add interest: distributed systems`
- `I'm interested in Rust`
- `Show my interests`
- `Remove interest LLM agents`

## On-demand digest

- `/check` — collect all new YouTube videos and GitHub releases since the last check
- `Check for new videos`

## Weekly digest subscription

- `Enable weekly digest` — subscribe to automatic weekly delivery
- `Disable weekly digest` — unsubscribe
- `Am I subscribed to weekly digest?` — check subscription status

Day-of-week and hour are controlled globally via `WEEKLY_DIGEST_DOW` and `WEEKLY_DIGEST_HOUR`
(see [configuration.md](./configuration.md)).

## Semantic search over your history

Powered by stored summary embeddings + pgvector cosine similarity.

- `What did I watch about Rust async runtimes?`
- `Find my videos on LLM evaluation from the last 2 weeks`
- `Remind me which video talked about pgvector indexes`

Search is scoped to the asking user — other users' history is never returned. Optional time windows accept
relative shorthand (`7d`, `2w`, `1m`) or an ISO date (`2026-05-01`).
