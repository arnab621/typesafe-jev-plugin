---
name: typesafe-jev-plugin:run-dataset
description: >
  Run a CSV, Excel, or text file dataset through a TypeSafe Jev solution signature,
  calling the TypeSafe API for each row and writing an Excel results file with input
  columns plus extracted answer columns. Use when the user says "run the dataset",
  "process the file", "run through Jev", "apply the signature to my data", "process
  these documents", "run this folder of files", or provides an input file path and
  a .sig.json path.
argument-hint: "--input <file.xlsx> --signature <file.sig.json> [--output <results.xlsx>] [--api-key <key>]"
allowed-tools:
  - AskUserQuestion
  - Bash
  - Read
---

# Run Dataset Through TypeSafe Jev

Process an input file row-by-row through a solution signature and produce a results Excel file.

---

## Step 1 — Gather inputs

If `--input` and `--signature` were not provided as arguments, use `AskUserQuestion` to ask:
- Path to the input (CSV/Excel file, a single `.txt`/`.md` file, or a directory of `.txt`/`.md` files)
- Path to the solution signature (.sig.json)
- Output path (optional — default: `<input>_results.xlsx` in the same directory)
- TypeSafe API key (optional — leave blank to use `TYPESAFE_API_KEY` env var)

**Text file mode:** if the input is a `.txt`/`.md` file or a directory, the runner processes each file as one row. The signature's state template must use `${file}` (full content) and/or `${filename}` (file name) instead of `${col:X}` placeholders. A "Source File" column is automatically added to the output.

---

## Step 2 — Check API key

If `--api-key` was provided as an argument, pass it directly to the script — skip the env var check.

Otherwise run:
```bash
echo ${TYPESAFE_API_KEY:+SET}
```

If the key is not set and no `--api-key` was provided, tell the user:
```
Provide your TypeSafe API key using one of:
  --api-key YOUR_KEY
  export TYPESAFE_API_KEY=your-key-here
```
Then stop — do not proceed without it.

---

## Step 3 — Validate signature

Always validate before processing:
```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_signature.py" "<signature_path>"
```

If validation fails, show the errors and stop. Offer to open the signature file for correction.

---

## Step 4 — Run the dataset

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/run_dataset.py" \
  --input "<input_path>" \
  --signature "<signature_path>" \
  --output "<output_path>" \
  [--api-key "<api_key_if_provided>"]
```

Show live output as rows are processed. The script prints progress per row and a final summary.

---

## Step 5 — Report results

After the run, summarise:
- Total rows / succeeded / errors / flagged for review
- Output file path
- If errors occurred: offer to show error details
- If rows were flagged: explain what the confidence threshold means and how to adjust it in the signature

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Column 'X' not found` | Column name in state_template doesn't match input | Check header names match `${col:X}` in signature; for text mode use `${file}` instead |
| `No .txt or .md files found` | Directory input is empty or has wrong extensions | Ensure the directory contains `.txt` or `.md` files |
| HTTP 401 | Bad API key | Verify `--api-key` value or `TYPESAFE_API_KEY` env var |
| HTTP 422 | Malformed question | Run validate_signature.py, check question schema |
| Empty output columns | Wrong dot-path in output_template | Check path against the API response structure |
