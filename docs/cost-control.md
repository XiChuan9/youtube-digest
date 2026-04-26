# Cost Control

The main paid surfaces are transcript fetching and LLM generation.

Controls in this project:

- `transcript.native_transcripts_only: true` sends Supadata `mode=native`.
- `max_videos_per_run` limits how many videos become LLM calls.
- `youtube.videos_per_channel` limits selection per channel.
- `generate --video-url ...` processes one explicit video without changing
  channel configuration.
- `generate --dry-run` discovers and filters videos without Supadata or LLM calls.
- `generate --reuse-transcript` looks for the latest
  `artifacts/*/<video_id>/raw_transcript.txt` and `transcript.json`, copies them
  into the current job, and skips Supadata for that video.
- `generate --reuse-analysis` looks for the latest
  `artifacts/*/<video_id>/analysis.md`, copies it into the current job, and skips
  the magazine analysis LLM pass for that video.
- Reuse is always explicit. When no matching artifact exists, generation falls
  back to the normal provider call.
- SQLite idempotency prevents duplicate processing unless `--force` is used.
- LLM provider/model/base URL are configurable, so users can choose lower-cost
  providers such as DeepSeek, local OpenAI-compatible servers, or Gemini Flash.

Recommended personal setup:

1. Run `generate --dry-run` first.
2. Keep `native_transcripts_only` enabled.
3. Start with `--limit 1` until prompts and output style are tuned.
4. Use `--reuse-transcript --reuse-analysis` when re-running the same video for
   packaging, archive, or non-prompt changes.
5. Review `artifacts/<job_id>/manifest.json` and `reuse.json` after each
   scheduled run.
