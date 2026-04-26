# Cost Control

The main paid surfaces are transcript fetching and LLM generation.

Controls in this project:

- `transcript.native_transcripts_only: true` sends Supadata `mode=native`.
- `max_videos_per_run` limits how many videos become LLM calls.
- `youtube.videos_per_channel` limits selection per channel.
- `generate --video-url ...` processes one explicit video without changing
  channel configuration.
- `generate --dry-run` discovers and filters videos without Supadata or LLM calls.
- SQLite idempotency prevents duplicate processing unless `--force` is used.
- LLM provider/model/base URL are configurable, so users can choose lower-cost
  providers such as DeepSeek, local OpenAI-compatible servers, or Gemini Flash.

Recommended personal setup:

1. Run `generate --dry-run` first.
2. Keep `native_transcripts_only` enabled.
3. Start with `--limit 1` until prompts and output style are tuned.
4. Review `artifacts/<job_id>/manifest.json` after each scheduled run.
