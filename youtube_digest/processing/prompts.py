"""Prompts for transforming transcripts into reader-friendly artifacts."""

from youtube_digest.models import Transcript, Video


VALID_MODES = {"faithful", "magazine", "summary"}


def build_transcript_analysis_prompt(
    video: Video,
    transcript: Transcript,
    min_words: int = 1800,
    max_words: int = 2500,
) -> str:
    return f"""You are an editorial analyst preparing a YouTube transcript for a long-form article.

The source may be an interview, podcast, lecture, panel, tutorial, documentary, product talk, debate, or solo essay. Adapt to the format. Do not assume the topic is technology.

VIDEO TITLE: {video.title}
CHANNEL: {video.channel}
VIDEO URL: {video.url}

VIDEO DESCRIPTION:
{video.description}

TRANSCRIPT SOURCE: {transcript.source}
TRANSCRIPT LANGUAGE: {transcript.language or "unknown"}

RAW TRANSCRIPT:
{transcript.text}

---

Read the full transcript before writing. Produce a structured editorial brief in Markdown using exactly these sections and headers:

Length requirement:
- Target {min_words}-{max_words} words for the editorial brief when the transcript is long enough.
- This brief is a writing contract, not a short summary. It must contain enough concrete material for a writer to produce a 3,000-5,000 word article without inventing.

## Source Format

Identify the format: interview, solo lecture, panel, tutorial, documentary, news analysis, or other. Identify the main speaker(s), interviewer/host if any, whose claims should be treated as the source of truth, and what kind of reader would need context.

## Core Arguments

Extract 4-7 load-bearing claims. These must be contestable positions or consequential interpretations, not generic topics. For each: **short title** + 4-6 sentences explaining the claim, the evidence, the caveats, the stakes, and how it connects to other claims.

## Logic Map

Explain how the arguments relate: linear chain, hub-and-spoke, tension model, problem-solution, chronology, or mixed. End with:
**Core tension**: [one sentence naming the most generative contradiction, tradeoff, or unresolved question.]

## Evidence and Examples

List 12-20 important concrete evidence points, examples, names, numbers, places, works, tools, dates, stories, comparisons, demonstrations, or counterexamples. Each item should be specific enough that a writer can reconstruct the substance without inventing.

## Golden Quotes

Extract 8-12 short quotes or near-quotes from the primary speaker(s). Choose lines that are concise, specific, and hard to paraphrase without losing force. If the transcript is imperfect, lightly repair obvious transcription errors, but do not fabricate quotes.

Format:
> "Quote text"
— [speaker if known, approximate location: early / mid / late]
[One sentence on why the quote matters.]

## Low-Value Material

Flag sections to cut or compress. Use these categories when applicable:
- Repetition
- Housekeeping or sponsor material
- Small talk
- Filler-heavy passages
- Tangents with little recoverable signal
- Overlong examples that can be compressed

For each: approximate location | category | one-line reason.

## Article Architecture

Propose 8-10 article sections for a {video.channel} reader who has not seen the original source. Each section must include:
- section title
- target length, usually 350-550 words
- which core argument it serves
- which evidence/examples belong there
- which golden quote(s), if any, belong there
- transition role: how it moves the article forward
- one paragraph describing what the section should actually say, not just what topic it covers

## Editorial Risks

List possible hallucination or distortion risks: ambiguous names, unclear causality, claims needing attribution, speaker uncertainty, domain-specific terms, or places where the transcript may be wrong.

Return only the editorial brief in Markdown.
"""


def build_article_from_outline_prompt(
    video: Video,
    transcript: Transcript,
    outline: str,
    min_words: int,
    max_words: int,
    section_min_words: int = 350,
    section_max_words: int = 550,
    min_sections: int = 8,
    max_sections: int = 10,
) -> str:
    return f"""You are a long-form magazine writer turning an editorial brief and source transcript into a substantial article.

VIDEO TITLE: {video.title}
CHANNEL: {video.channel}
VIDEO URL: {video.url}

VIDEO DESCRIPTION:
{video.description}

TRANSCRIPT SOURCE: {transcript.source}
TRANSCRIPT LANGUAGE: {transcript.language or "unknown"}

EDITORIAL BRIEF:
{outline}

RAW TRANSCRIPT FOR FACT-CHECKING:
{transcript.text}

---

Write the article in clean Markdown.

Length and depth:
- Target {min_words}-{max_words} words. Stay within +/-10% unless the transcript is too short to support it.
- Use {min_sections}-{max_sections} major sections when the source is long enough.
- Each major section should be {section_min_words}-{section_max_words} words. Treat this as a hard structural constraint, not a suggestion.
- A section is too short if it only defines a topic. Each section must contain claim, context, evidence/example, quote or paraphrase where useful, analysis, and transition.
- Do not silently drop any Core Argument from the editorial brief. If one must be compressed, preserve its claim and consequence.

Fidelity:
- The editorial brief controls structure; the transcript controls facts.
- Do not add new arguments, examples, facts, or causal claims that are not supported by the transcript.
- Preserve uncertainty and caveats. If the speaker is tentative, write tentatively.
- Attribute contested or speaker-specific claims instead of presenting them as settled fact.

Style:
- Avoid corporate blog language, marketing sheen, and generic praise.
- Prefer analytical narration: specific, concrete, skeptical where appropriate, and close to the speaker's reasoning.
- Keep enough texture that the reader feels the source conversation or talk had a human shape: tensions, detours, examples, hesitations, and moments of emphasis.
- Explain jargon only when it helps the reader follow the argument.

Quotes:
- Use the strongest Golden Quotes from the brief.
- Frame each quote before it and analyze it after it.
- Do not cluster all quotes in one section.

Structure:
- Start with a title that reflects the central tension, not a slogan.
- Use Markdown headings.
- Include explicit transitions between major sections.
- Do not include source notes; the EPUB builder adds those separately.

Return only the finished article in Markdown.
"""


def build_article_expansion_prompt(
    video: Video,
    transcript: Transcript,
    outline: str,
    draft: str,
    current_words: int,
    min_words: int,
    max_words: int,
    section_min_words: int = 350,
    section_max_words: int = 550,
) -> str:
    return f"""You are revising a magazine article that is too short for its source material.

The current draft is {current_words} words. It must be expanded to at least {min_words} words and should ideally land between {min_words}-{max_words} words.

VIDEO TITLE: {video.title}
CHANNEL: {video.channel}
VIDEO URL: {video.url}

EDITORIAL BRIEF:
{outline}

CURRENT DRAFT:
{draft}

RAW TRANSCRIPT FOR FACT-CHECKING:
{transcript.text}

---

Rewrite and expand the full article in clean Markdown.

Expansion requirements:
- Do not merely add a conclusion or pad with generalities. Expand the body.
- Make each major section {section_min_words}-{section_max_words} words where the source supports it.
- Add missing evidence, concrete examples, caveats, speaker reasoning, transitions, and quote analysis from the editorial brief and transcript.
- Preserve all existing good material, but replace corporate-blog abstractions with specific claims and transcript-grounded detail.
- Do not add facts, examples, or claims unsupported by the transcript.
- Keep the same article purpose: a deep, cross-domain, interview-derived long read.
- Do not include source notes; the EPUB builder adds those separately.

Return only the complete revised article in Markdown.
"""


def build_article_prompt(
    video: Video,
    transcript: Transcript,
    mode: str,
    min_words: int = 3000,
    max_words: int = 5000,
) -> str:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")

    mode_instructions = {
        "faithful": """
Create a faithful cleaned reading edition of the transcript.
- Preserve all substantive claims, examples, caveats, named entities, and sequence of ideas.
- Remove filler, false starts, repeated phrases, sponsor chatter, and purely conversational noise.
- Add headings and paragraph breaks, but do not turn this into a short summary.
- If a detail is uncertain, keep the uncertainty instead of inventing clarity.
""",
        "magazine": f"""
Turn the transcript into a deep, interview-driven long read.
- Target a substantial article, roughly {min_words}-{max_words} words when the transcript is long enough. Do not collapse a long interview, lecture, panel, tutorial, or documentary into a short executive summary.
- Adapt to the subject matter. For any domain, identify the central problem, the speaker's main claims, the evidence or examples they use, the context a reader needs, the strongest objections or caveats, and what changes if the speaker is right.
- Preserve the chain of reasoning: how the speaker gets from one claim to the next, including assumptions, caveats, tradeoffs, disagreements, failed attempts, and unresolved questions.
- Keep the texture of the source. Include concrete examples, named people, organizations, places, works, tools, numbers, timelines, anecdotes, and surprising asides instead of smoothing them into generic takeaways.
- Use quotes selectively, but preserve the speaker's strongest formulations. Clean filler words without making the quotes sound like PR copy.
- Explain jargon and obscure references for smart non-specialists, but do it in the flow of the article rather than as a glossary.
- You may reorder material for readability, but do not erase important detours simply because they are messy. If a detour reveals how the speaker thinks, keep it.
- Avoid corporate blog language, marketing sheen, breathless hype, and phrases like "quiet revolution", "game changer", "unlocking value", or "reimagining the future" unless the speaker explicitly says them and they matter.
- Write with an analytical magazine voice: curious, specific, skeptical where appropriate, and grounded in the transcript. Prefer concrete nouns and verbs over abstract praise.
- Include enough connective tissue that the article reads as a reconstruction of the conversation's substance, not a list of conclusions.
- If the transcript is very long, prioritize unique ideas, important examples, moments of tension, and claims with consequences. Compress only repetition, housekeeping, sponsor reads, and verbal filler.
- Do not write "in this video"; the article must stand alone.
""",
        "summary": """
Create a concise executive briefing.
- Focus on key ideas, evidence, caveats, decisions, and action items.
- Use clear headings and compact bullets where helpful.
- Keep named entities and specific claims accurate.
- Avoid decorative prose.
""",
    }[mode].strip()

    return f"""You are an expert editor creating reader-friendly articles from YouTube transcripts.

VIDEO TITLE: {video.title}
CHANNEL: {video.channel}
VIDEO URL: {video.url}

VIDEO DESCRIPTION:
{video.description}

TRANSCRIPT SOURCE: {transcript.source}
TRANSCRIPT LANGUAGE: {transcript.language or "unknown"}

RAW TRANSCRIPT:
{transcript.text}

---

{mode_instructions}

Use the title and description to correct transcript spelling for people, companies, products, and technical terms.
Return clean Markdown only.
"""
