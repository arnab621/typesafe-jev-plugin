# typesafe-jev-plugin

A Claude (Codex to follow soon) plugin that lets you build reusable schemas **(solution signatures)** for any classification or scoring problem, then run data from CSV, Excel, or text file datasets through the [TypeSafe AI](https://typesafe.ai/) API and export structured results to Excel — all from within Claude Code or Cowork.

---

## What is TypeSafe Jev?

[source] (https://docs.typesafe.ai/introduction)

Jev from Typesafe.ai is a "System One" AI model that returns **typed, calibrated judgments** instead of generating text. You define what to classify (a Choice), score (a Score), or verify (a Noul), and Jev returns a structured answer with a probability distribution — fast, cheap, and directly consumable by code.

This plugin wraps that API into a two-step workflow:

1. **Create a signature** — describe your use case via an iteractive mode; the plugin generates a `.sig.json` file that includes the state and questions.
2. **Run a dataset** — point the signature JSON at a CSV or Excel file; the plugin calls Jev for every row (for excel/csv data) and writes results back based on your output template signature.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| [Claude Code](https://claude.ai/code) | Plugin host |
| [Claude or Cowork](https://claude.ai) | Plugin host |
| TypeSafe API key | Sign up at [typesafe.ai](https://typesafe.ai) |
| Python 3.9+ | Must be on your PATH |
| `requests` + `openpyxl` | `pip install requests openpyxl` |

---

## Installation

**Install the plugin permanently:**
```
/plugin install /path/to/typesafe-jev-plugin
```

**Or load for a single session:**
```bash
cc --plugin-dir /path/to/typesafe-jev-plugin
```

**Verify it loaded:**
```
/plugin
```
You should see `typesafe-jev-plugin` listed with two skills: `create-signature` and `run-dataset`.

---

## Quick Start

### Step 1 — Set your API key
```bash
export TYPESAFE_API_KEY=your-key-here
```

### Step 2 — Create a solution signature
```
/typesafe-jev-plugin:create-signature
```
Claude will guide you interactively through defining:
- The **input mode** — column-based (CSV/Excel) or text file analysis (`.txt`/`.md`/directory)
- The **state schema** — which columns or file content map to state fields
- The **questions** — what Jev should judge (Choice, Score, or Noul)
- The **output template** — which answer fields appear as columns in your results

The result is a `.sig.json` file you can reuse and share.

### Step 3 — Run your dataset
```
/typesafe-jev-plugin:run-dataset --input reviews.xlsx --signature travel_review.sig.json
```
Results are written to `products_results.xlsx` with your original data plus Jev's answers appended as new columns.

---

## Ready-to-Use Examples

Three ready-to-use signatures are included in `examples/`:

| File | Mode | What it does |
|---|---|---|
| `travel_review.sig.json` | Column-based | Analyses travel reviews for sentiment, aspect, traveller type, and recommendation strength |
| `llm_guardrail.sig.json` | Column-based | Detects jailbreak attempts, identifies rule violated, scores severity |
| `support_agent_review.sig.json` | Text file | Audits AI agent session traces for resolution, policy adherence, and CSAT |
| `document_review.sig.json` | Text file | Reviews papers/reports across methodology, argument, evidence, and originality; produces editorial recommendation |

**Input Excel** (column headers must match exactly):

| Destination | Review |
|---|---|
| Santorini, Greece | The sunsets from Oia were breathtaking. Stayed at a cliffside villa — worth every penny. Crowds in August are intense though, go in May. |
| Bangkok, Thailand | Street food is unreal — pad thai at 2am for next to nothing. Tuk-tuk drivers tried to scam us twice but otherwise amazing value. Would go back. |
| Venice, Italy | Overpriced and overcrowded. Gondola was €90 for 30 minutes. The city is stunning but feels like a theme park now. Skip peak season. |

**Run it:**
```
/typesafe-jev-plugin:run-dataset \
  --input reviews.xlsx \
  --signature examples/travel_review.sig.json \
  --api-key ts-xxxxxxxxxxxx
```

**Output Excel:**

| Destination | Review | Sentiment | Sentiment Conf | Aspect Focus | Traveller Type | Recommendation | Genuine Review | Needs Response | Flag for Review |
|---|---|---|---|---|---|---|---|---|---|
| Santorini, Greece | ... | positive | 0.89 | overall_experience | couple | Highly recommends | 0.95 | No | No |
| Bangkok, Thailand | ... | mixed | 0.82 | food_dining | couple | Neutral or conditional | 0.88 | No | No |
| Venice, Italy | ... | negative | 0.86 | value_for_money | solo | Leans negative | 0.91 | Yes | No |

A **Summary** sheet is also added with totals: rows processed, succeeded, errors, and rows flagged for low-confidence review.

---

## Text File Analysis

In addition to CSV/Excel, the plugin can process **full-text documents** — resumes, contracts, reports, narratives — running multiple classification tasks against each document in a single API call.

### Input modes

| Input | What happens |
|---|---|
| `--input document.txt` | Single file → one result row |
| `--input docs/` | Directory → one row per `.txt`/`.md` file |

### State template placeholders

```json
"state_template": {
  "resume": "${file}"
}
```

| Placeholder | Expands to |
|---|---|
| `${file}` | Full text content of the current file |
| `${filename}` | Name of the file (e.g. `resume.txt`) |

### Example: Resume screening signature

```json
{
  "name": "Resume Screener",
  "model": "jev-1.13.0",
  "state_template": {
    "resume": "${file}"
  },
  "questions": {
    "primary_talent_profile": {
      "type": "choice",
      "instructions": "Pick the best match for the candidate's talent profile.",
      "criteria": {
        "frontend_engineer": "Builds user-facing interfaces: React, Vue, Angular...",
        "backend_engineer": "Builds server-side services, APIs, databases...",
        "full_stack_engineer": "Ships both UI and services on the same projects...",
        "ml_ai_engineer": "Trains, fine-tunes, evaluates, or serves ML/LLM models..."
      }
    },
    "technical_depth": {
      "type": "score",
      "instructions": "Rate hands-on engineering depth from the experience bullets.",
      "criteria": [
        "No coding — adjacent roles only",
        "Coursework or tutorial projects only",
        "Small scoped work inside someone else's design",
        "Owns features end-to-end with little supervision",
        "Owns whole systems and makes architecture tradeoffs",
        "Deep specialist: OSS maintainer, systems internals, org-wide architecture"
      ]
    },
    "mentorship_demonstrated": {
      "type": "noul",
      "instructions": "Does the resume demonstrate mentoring experience?"
    }
  },
  "output_template": {
    "columns": [
      { "header": "Profile",         "path": "answers.primary_talent_profile.choice" },
      { "header": "Profile Conf",    "path": "answers.primary_talent_profile.confidence" },
      { "header": "Tech Depth",      "path": "answers.technical_depth.score" },
      { "header": "Mentorship",      "path": "answers.mentorship_demonstrated.noul" },
      { "header": "Needs Review",    "type": "confidence_flag", "path": "answers.primary_talent_profile.confidence", "threshold": 0.65 }
    ]
  }
}
```

**Run it against a directory of resumes:**
```
/typesafe-jev-plugin:run-dataset --input resumes/ --signature resume_screener.sig.json
```

The output Excel will have a **Source File** column (the filename) prepended automatically, followed by all your defined output columns.

---

## Solution Signature Format

A `.sig.json` file is a plain JSON file with four sections:

```json
{
  "name": "Travel Review Analysis",
  "description": "Analyses travel reviews for sentiment, aspect, traveller type, and recommendation",
  "version": "1.0.0",
  "model": "jev-1.13.0",
  "state_template": { ... },
  "questions": { ... },
  "output_template": { ... }
}
```

### state_template — mapping columns to state

Use `${col:Column Name}` placeholders. The runner substitutes the value from that column for each row:

```json
"state_template": {
  "destination": "${col:Destination}",
  "review":      "${col:Review}"
}
```

The template can be nested as deeply as needed. Placeholder names must match your input file's column headers exactly.

### questions — what Jev judges

Three question types, all running in parallel per row:

**Choice** — pick one from a defined set. Criteria can be plain strings or structured objects with `what`, `not_for`, and `examples`:
```json
"sentiment": {
  "type": "choice",
  "instructions": "What is the overall sentiment expressed in `review`?",
  "criteria": {
    "positive": {
      "what": "The reviewer is broadly satisfied — praise outweighs any criticism.",
      "not_for": "Reviews that balance positives and negatives roughly equally.",
      "examples": ["Absolutely loved it, would go back in a heartbeat", "One of the best trips we've ever taken"]
    },
    "negative": {
      "what": "The reviewer is broadly dissatisfied — complaints outweigh any positives.",
      "examples": ["Would not recommend, complete waste of money", "So disappointed — nothing lived up to the hype"]
    },
    "mixed": "The reviewer expresses clearly conflicting feelings with roughly equal weight on both sides."
  }
}
```

**Noul** — probability that something is true (`true` and `false` keys only):
```json
"is_eligible": {
  "type": "noul",
  "instructions": "Does the narrative describe genuine technological uncertainty?",
  "criteria": {
    "true": "The uncertainty is technological and couldn't be resolved by known methods",
    "false": "The challenge is operational or resolvable by standard techniques"
  }
}
```

**Score** — degree along a spectrum (ordered list of level descriptions, lowest to highest):
```json
"recommendation_strength": {
  "type": "score",
  "instructions": "How strongly does the review recommend or discourage visiting the destination?",
  "criteria": [
    "Actively discourages: explicitly warns others away or says they would not return.",
    "Leans negative: more dissatisfied than satisfied; would not enthusiastically recommend.",
    "Neutral or conditional: recommends with significant caveats, or neither recommends nor discourages.",
    "Leans positive: broadly recommends but notes meaningful drawbacks worth knowing.",
    "Highly recommends: enthusiastically endorses with little or no reservation."
  ]
}
```

### output_template — what columns appear in the results Excel

```json
"output_template": {
  "columns": [
    { "header": "Sentiment",      "path": "answers.sentiment.choice" },
    { "header": "Confidence",     "path": "answers.sentiment.confidence" },
    { "header": "Recommendation", "path": "answers.recommendation_strength.score" },
    { "header": "Genuine Review", "path": "answers.genuine_review.noul" },
    { "header": "Flag for Review","type": "confidence_flag", "path": "answers.sentiment.confidence", "threshold": 0.65 }
  ]
}
```

**Column types:**

| Type | Description |
|---|---|
| `path` (default) | Extracts a value using a dot-path into the API response |
| `confidence_flag` | Writes `Yes` if the value at `path` is below `threshold` (default `0.6`) |

**Common dot-paths:**

| Answer field | Path |
|---|---|
| Chosen option | `answers.<id>.choice` |
| Confidence (0–1) | `answers.<id>.confidence` |
| Full probability distribution | `answers.<id>.probabilities` |
| Noul probability | `answers.<id>.noul` |
| Score level | `answers.<id>.score` |

---

## Commands

| Command | What it does |
|---|---|
| `/typesafe-jev-plugin:create-signature` | Interactive guided flow to create a `.sig.json` |
| `/typesafe-jev-plugin:run-dataset --input <file_or_dir> --signature <file.sig.json> [--output <file>] [--api-key <key>]` | Run a dataset and write results to Excel. Input can be CSV/Excel, a single `.txt`/`.md`, or a directory of `.txt`/`.md` files. |

---

## Agents

Two agents activate automatically when relevant:

| Agent | Triggers when... |
|---|---|
| `signature-designer` | You describe a classification problem and need help designing the questions |
| `signature-validator` | You ask to check a `.sig.json`, or a run fails with a schema error |

---

## Scripts (direct use without Claude Code)

```bash
# Validate a signature
python scripts/validate_signature.py my.sig.json

# Run a dataset
python scripts/run_dataset.py \
  --input data.xlsx \
  --signature my.sig.json \
  --output results.xlsx \
  --api-key ts-xxxxxxxxxxxx
```

---

## File Structure

```
typesafe-jev-plugin/
├── .claude-plugin/
│   └── plugin.json                     # Plugin manifest
├── skills/
│   ├── create-signature/SKILL.md       # /typesafe-jev-plugin:create-signature
│   └── run-dataset/SKILL.md            # /typesafe-jev-plugin:run-dataset
├── agents/
│   ├── signature-designer.md           # Helps design state + questions
│   └── signature-validator.md          # Validates .sig.json files
├── hooks/
│   ├── hooks.json                      # Auto-validates .sig.json on save
│   └── scripts/validate_on_save.py
├── scripts/
│   ├── run_dataset.py                  # Main runner
│   ├── typesafe_client.py              # HTTP API layer (swap here for SDK)
│   └── validate_signature.py           # Signature validator CLI
└── examples/
    ├── travel_review.sig.json          # Travel review analysis (column-based)
    ├── llm_guardrail.sig.json          # LLM policy guardrail (column-based)
    ├── support_agent_review.sig.json   # AI agent session audit (text file mode)
    └── document_review.sig.json        # Paper/report review and scoring (text file mode)
```

---

## Extending the Plugin

**To support a new input format** (e.g. PDF): add a reader function to `scripts/run_dataset.py` alongside `read_csv` and `read_excel`, then register its extension in `read_input`.

**To switch to the TypeSafe Python SDK**: replace only the body of `call_api` in `scripts/typesafe_client.py`. The function signature stays the same so nothing else changes.

**To add a new output column type**: add a new `elif col_type == "your_type"` branch in `extract_output_row` in `scripts/run_dataset.py`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Column 'X' not found` | Placeholder name doesn't match input header | Ensure `${col:X}` matches your file's column header exactly (case-sensitive); for text mode use `${file}` instead |
| `No .txt or .md files found` | Directory input has no text files | Ensure the directory contains `.txt` or `.md` files |
| HTTP 401 | Bad API key | Check `--api-key` value or `TYPESAFE_API_KEY` env var |
| HTTP 422 | Malformed question | Run `validate_signature.py`, fix reported errors |
| Empty output columns | Wrong dot-path in `output_template` | Verify path matches question ID and a valid response field |
| Noul schema error | Extra keys in noul criteria | Only `"true"` and `"false"` are valid noul criteria keys |
| Score schema error | Score criteria is an object, not a list | Score criteria must be a JSON array of strings |

---

## Resources

- [TypeSafe documentation](https://docs.typesafe.ai)
- [TypeSafe API reference](https://docs.typesafe.ai/api.md)
- [TypeSafe Python SDK](https://docs.typesafe.ai/sdk/python.md)
- [Available models](https://docs.typesafe.ai/models.md)
