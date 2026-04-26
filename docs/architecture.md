# Architecture

The product boundary is the `youtube_digest` package plus the `youtube-digest`
CLI. Hermes, cron, systemd, dashboards, and future MCP servers should call that
boundary instead of importing internal modules.

```mermaid
flowchart TD
  A["Hermes Skill / CLI / Cron / API"] --> B["youtube_digest.pipeline"]
  B --> C["Selection: channels or explicit video URL"]
  C --> J["Discovery metadata: YouTube Data API"]
  B --> D["Transcript Provider: Supadata"]
  B --> E["Transcript Analysis"]
  E --> I["Article Writer: OpenAI-compatible / Gemini / Anthropic"]
  B --> F["EPUB Builder"]
  B --> G["Delivery"]
  B --> H["SQLite + Artifacts"]
```

Design principles:

- Keep API keys in environment variables or `.env`, never config files.
- Save every intermediate artifact so output can be audited.
- Magazine mode uses an analysis-to-article workflow by default, then checks
  output length and triggers an expansion pass when the draft is too short.
- Default to native transcripts to avoid surprise transcription charges.
- Keep LLM providers pluggable; OpenAI-compatible chat completions are the
  default integration surface.
- Make paid operations explicit and bounded.
- Keep Hermes integration thin; the CLI remains the stable contract.
