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
/typesafe-jev-plugin:run-dataset --input products.xlsx --signature vat.sig.json
```
Results are written to `products_results.xlsx` with your original data plus Jev's answers appended as new columns.

---

## Ready-to-Use Examples

Three ready-to-use signatures are included in `examples/`:

| File | Mode | What it does |
|---|---|---|
| `vat_classification.sig.json` | Column-based | Classifies products into UK VAT categories |
| `llm_guardrail.sig.json` | Column-based | Detects jailbreak attempts, identifies rule violated, scores severity |
| `support_agent_review.sig.json` | Text file | Audits AI agent session traces for resolution, policy adherence, and CSAT |
| `document_review.sig.json` | Text file | Reviews papers/reports across methodology, argument, evidence, and originality; produces editorial recommendation |

**Input Excel** (column headers must match exactly):

| Product Name | Description |
|---|---|
| Jaffa Cakes 12-pack | Round sponge with orange jelly, half-coated in dark chocolate |
| Organic whole milk 2L | Fresh pasteurised full-fat cow's milk |
| Children's school shoes size 3 | Leather school shoes, UK child's size 3 |

**Run it:**
```
/typesafe-jev-plugin:run-dataset \
  --input products.xlsx \
  --signature examples/vat_classification.sig.json \
  --api-key ts-xxxxxxxxxxxx
```

**Output Excel:**

| Product Name | Description | VAT Category | VAT Confidence | Intended Use | Use Confidence | Needs Review |
|---|---|---|---|---|---|---|
| Jaffa Cakes 12-pack | ... | standard_rated | 0.74 | retail_home_consumption | 0.92 | No |
| Organic whole milk 2L | ... | zero_food | 0.97 | retail_home_consumption | 0.95 | No |
| Children's school shoes size 3 | ... | zero_children_clothing | 0.91 | children_specific | 0.96 | No |

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
  "name": "UK VAT Classification",
  "description": "Classifies products into HMRC VAT categories",
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
  "product": {
    "name": "${col:Product Name}",
    "description": "${col:Description}"
  }
}
```

The template can be nested as deeply as needed. Placeholder names must match your input file's column headers exactly.

### questions — what Jev judges

Three question types, all running in parallel per row:

**Choice** — pick one from a defined set:
```json
"vat_category": {
  "type": "choice",
  "instructions": "Classify the product in `product` into the correct UK VAT category.",
  "criteria": {
    "zero_food": "Zero-rated at 0% — basic food for human consumption...",
    "standard_rated": "Standard-rated at 20% — default for goods not in another category..."
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

**Score** — degree along a spectrum (ordered list of level descriptions):
```json
"novelty_level": {
  "type": "score",
  "instructions": "Rate the novelty of the advance claimed.",
  "criteria": [
    "Standard application of well-known techniques",
    "Known techniques in a new context",
    "Non-obvious combination requiring experimentation",
    "Extends the state of the art meaningfully",
    "Genuinely novel — publishable or patentable"
  ]
}
```

### output_template — what columns appear in the results Excel

```json
"output_template": {
  "columns": [
    { "header": "VAT Category",  "path": "answers.vat_category.choice" },
    { "header": "Confidence",    "path": "answers.vat_category.confidence" },
    { "header": "Needs Review",  "type": "confidence_flag", "path": "answers.vat_category.confidence", "threshold": 0.6 }
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
    ├── vat_classification.sig.json     # UK VAT classification (column-based)
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
