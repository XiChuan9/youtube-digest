# Content Modes

`faithful`

Creates a cleaned reading edition of the transcript. It removes filler and
repairs structure but should preserve substantive claims, examples, caveats, and
the original sequence of ideas.

`magazine`

Creates a polished long-form article. By default this mode uses a two-pass
process:

1. Build a structured editorial brief from the transcript.
2. Write the article from that brief while fact-checking against the transcript.
3. Check the article length and run an expansion pass when it falls below 85% of
   the configured minimum.

This mode may compress repetition and reorder ideas for readability. It is not a
verbatim transcript and should be labeled as a rewritten article based on the
source video. The intermediate `analysis.md`, `article_draft.md`, and optional
`article_expanded_*.md` artifacts are saved for auditing.

Relevant configuration:

```json
"content": {
  "analysis_min_words": 1800,
  "analysis_max_words": 2500,
  "magazine_min_words": 3000,
  "magazine_max_words": 5000,
  "magazine_section_min_words": 350,
  "magazine_section_max_words": 550,
  "magazine_min_sections": 8,
  "magazine_max_sections": 10,
  "magazine_expansion_passes": 1,
  "magazine_two_pass": true
}
```

`summary`

Creates a concise briefing with key points, caveats, decisions, and action
items.

For all modes, the raw transcript is saved under the job artifact directory.
