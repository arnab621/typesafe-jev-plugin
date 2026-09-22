---
name: typesafe-jev-plugin:create-signature
description: >
  Create a TypeSafe Jev solution signature — a reusable .sig.json file that defines
  the state schema, questions (Choice/Score/Noul), and output template for a
  classification or scoring use case. Use when the user says "create a signature",
  "build a signature", "set up a TypeSafe solution", "design a Jev pipeline", or
  describes a classification or scoring problem they want to run against a dataset.
argument-hint: "[use case name or description]"
allowed-tools:
  - AskUserQuestion
  - Write
  - Read
  - Bash
---

# Create TypeSafe Jev Solution Signature

Guide the user interactively to produce a `.sig.json` solution signature file.
Use `AskUserQuestion` at every decision point — do not ask multiple questions in prose.
Build the JSON structure progressively across the steps below and save when complete.

---

## Step 1 — Basic information

Use `AskUserQuestion` to ask:
- What is the name of this solution? (e.g. "UK VAT Classification")
- A one-sentence description of what it classifies or scores

Then ask where to save the file. Suggest `<kebab-case-name>.sig.json` in the current directory.

---

## Step 2 — Input mode and state schema

### 2a — Input mode

Use `AskUserQuestion` to ask what kind of input data this signature will be used with:

- **Column-based (tabular)** — input is a CSV or Excel file; each row has named columns. Use `${col:Column Name}` placeholders in the state template.
- **Text file analysis** — input is one or more `.txt` or `.md` files (e.g. resumes, contracts, reports, narratives). Jev receives the full file content as a text blob. Use `${file}` and `${filename}` placeholders.

### 2b — State schema (column-based mode)

Explain to the user: the state is the JSON context Jev receives for each row. It maps columns from the input file into a structured JSON object using `${col:Column Name}` placeholders.

Use `AskUserQuestion` to ask:
- What columns from the input file should be included?

For each column:
- What should it be named in the state JSON? (show a nested example — e.g. column "Product Name" → `product.name` → `"name": "${col:Product Name}"`)

Build the `state_template` dict progressively. After each column, ask "Add another field?" with options Yes / No.

Show the assembled `state_template` and ask for confirmation before moving on:

```json
{
  "product": {
    "name": "${col:Product Name}",
    "description": "${col:Description}"
  }
}
```

### 2c — State schema (text file analysis mode)

Explain to the user: in text mode the runner reads each `.txt` or `.md` file and passes its full content to Jev. Two special placeholders are available:

| Placeholder | Expands to |
|---|---|
| `${file}` | Full text content of the file |
| `${filename}` | Name of the file (e.g. `resume.txt`) |

Ask the user: what key should the text be stored under in the state? (e.g. `resume`, `document`, `narrative`)

Build the `state_template` using their chosen key:

```json
{
  "resume": "${file}"
}
```

You can nest it or combine with `${filename}` for context:

```json
{
  "document": {
    "filename": "${filename}",
    "content":  "${file}"
  }
}
```

Show the assembled `state_template` and ask for confirmation before moving on.

**Running in text mode:**
- Single file: `--input resume.txt --signature my.sig.json`
- Directory of files: `--input resumes/ --signature my.sig.json` (processes every `.txt`/`.md` in the directory)
- Output always goes to an Excel file with a "Source File" column prepended automatically.

---

## Step 3 — Questions

Explain: questions are the judgments Jev makes for each row. They all run in parallel in one API call.

For each question, use `AskUserQuestion` in sequence:

**3a — Question ID**
Ask for a snake_case identifier (e.g. `vat_category`, `novelty_level`). This becomes the key in the questions object and the prefix for output columns.

**3b — Question type**
Use `AskUserQuestion` with options:
- Choice — pick one option from a defined set (returns: choice, confidence, probabilities)
- Noul — probability that something is true (returns: noul probability 0–1)
- Score — degree along a described spectrum (returns: score level, confidence)

**3c — Instructions**
Ask: what is the judgment being asked? (one clear sentence)

**3d — Criteria** (varies by type):

For **Choice**: first use `AskUserQuestion` to ask whether the criteria should be:
- **Simple** — a plain string description per option (quick, works for straightforward sets)
- **Structured** — an object with `what`, optional `not_for`, and optional `examples` per option (recommended for complex or easily-confused categories, e.g. tax, legal, compliance)

Then collect named options one by one. For each option ask:
- Option key (snake_case)
- If **simple**: a single description string
- If **structured**:
  - `what`: what this option means (required)
  - `not_for`: what explicitly does NOT qualify (optional — use when boundaries are often confused)
  - `examples`: a list of concrete examples (optional but strongly recommended)

Ask "Add another option?" until done. Always suggest including an `"other"` or `"unclear"` option.

Both formats are valid and accepted by the TypeSafe API. Structured criteria produce more precise judgments when options are similar or have important exclusions. The `what`/`not_for`/`examples` field names are user-defined conventions — the model sees both the names and values, so choose labels that clarify intent.

For **Noul**: use `AskUserQuestion` to collect exactly two descriptions:
- What does `true` mean for this question?
- What does `false` mean?
Only `true` and `false` are valid keys — enforce this silently.

For **Score**: collect level descriptions as an ordered list. Ask for each level from lowest to highest. Ask "Add another level?" until done (minimum 2, typically 3–5).

After completing each question, ask "Add another question?" with options Yes / No.

---

## Step 4 — Output template

Explain: the output template defines which columns appear in the results Excel file. Values are extracted from each Jev API response using dot-paths.

Common paths for a question with id `<qid>`:
- `answers.<qid>.choice` — the chosen option (Choice questions)
- `answers.<qid>.confidence` — how concentrated the probability distribution is (0–1)
- `answers.<qid>.noul` — the probability of true (Noul questions)
- `answers.<qid>.score` — the weighted score level (Score questions)

Use `AskUserQuestion` to suggest columns based on the questions defined:
- For each Choice/Score question: suggest a column for `.choice`/`.score` and one for `.confidence`
- For each Noul question: suggest a column for `.noul`
- Offer to add a `confidence_flag` column (type: `confidence_flag`) for any question where low confidence should be flagged for human review

For each column collect:
- Header name (how it appears in Excel)
- Type: `path` (default) or `confidence_flag`
- Path into the response (e.g. `answers.vat_category.choice`)
- For `confidence_flag`: threshold value (default 0.6)

Ask "Add another output column?" until done.

---

## Step 5 — Model

Use `AskUserQuestion` to ask which TypeSafe model to use.
Default: `jev-1.13.0`
Note: check https://docs.typesafe.ai/models.md for current available models.

---

## Step 6 — Assemble, review, save, validate

Assemble the complete signature JSON:

```json
{
  "name": "<name>",
  "description": "<description>",
  "version": "1.0.0",
  "model": "<model>",
  "state_template": { ... },
  "questions": { ... },
  "output_template": {
    "columns": [ ... ]
  }
}
```

Show the full JSON to the user and ask for confirmation before saving.

Write the file to the chosen path, then validate it:
```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_signature.py" "<path>"
```

If validation fails, show the errors, fix them, and re-save.
If validation passes, confirm the file is ready and show the command to run a dataset:
```
/typesafe-jev-plugin:run-dataset --input <your-data.xlsx> --signature <path>
```

---

## Template fallback

If the user says they prefer to edit a template manually, generate and save a commented
template `.sig.json` with placeholder values and inline comments explaining each field,
then open it for the user to edit. Validate after they confirm they're done.
