# The Macrochip

A weekly newsletter in Spanish explaining the global economic and geopolitical context driving the markets — for someone with no background in economics, never giving investment advice.

Every Sunday, a Claude Code scheduled task downloads hard data from official sources, researches and writes the week's report, verifies it against its own sources by re-reading them (not from memory), validates it with deterministic rules, and creates a **draft** — never sends it — in Buttondown. A human reviews it and sends it.

## The pipeline

```
fetch_data.py → datos.json
      ↓
[writing + verification — require judgment, done by Claude]
      ↓
validate.py → valid informe.json, or stops without publishing
      ↓
render.py → informe.md (email) + transparencia.md (internal use)
      ↓
publish.py → draft in Buttondown
```

The line is deliberate: anything that can be decided by a fixed rule is Python code with tests (downloading, validation, rendering, publishing). Anything that needs real judgment — what counts as news, whether a source says what it appears to say, whether a figure checks out — is done by Claude inside the scheduled task, following versioned instructions in the repo, not code trying to simulate judgment.

A single `informe.schema.json` is the source of truth: the email, the AI context package carrying every figure, and the transparency summary all come from the same JSON — never written separately.

## Engineering decisions

**Where there's no official source, the risk gets documented instead of pretended away.** ECB, Eurostat, INE and FRED cover interest rates and inflation with no friction. For the Nikkei 225, gold and the MSCI indices there's no free official API; Yahoo Finance's unofficial endpoint is used instead, with the risk explicitly noted instead of ignored, and no speculative backup source for a failure that hasn't happened — if it does, the pipeline stops without publishing, same as any other failure.

**Verification is a real second pass, not a formality.** After writing, a separate session re-reads every source from scratch — without trusting what the writing step remembered — and checks every figure against the hard data before signing off on the report.

**Transparency is generated, but not sent.** The report records which sources were used, which were discarded, and what the verifier corrected. But showing that list of corrections to every subscriber signals "this has flaws" rather than reliability, so that section is written separately, for internal use only, never in the email.

**Unit tests + one real end-to-end run.** Besides unit tests (validation logic, data parsing, mocked HTTP calls), the pipeline was tested in full with real data and a real draft created in Buttondown — that's what surfaces the integration failures a single isolated test never sees.

## Architecture

```
config/        # Everything editable without touching code: modules, sources, markets, style
prompts/        # Writer, verifier, style — the versioned judgment
schema/          # informe.schema.json, the core data contract
scripts/          # Thin CLIs
src/briefing/      # The real logic, with tests
data/AAAA-Sww/      # One folder per week: data, draft, report, email, log
```

The project's full conventions — why each decision was made, what was ruled out and why — live in [`CLAUDE.md`](./CLAUDE.md).

## Stack

Python 3.11+, minimal dependencies (`requests`, `PyYAML`, `jsonschema`), no frameworks, with unit tests.

## Disclaimer

Informational content. Not investment advice.
