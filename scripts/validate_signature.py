"""
Validate a TypeSafe Jev solution signature (.sig.json) file.

Usage: python validate_signature.py <path/to/signature.sig.json>
Exit 0 = valid, Exit 1 = invalid.
"""

import json
import sys

REQUIRED_TOP_LEVEL = ["name", "model", "state_template", "questions"]
VALID_QUESTION_TYPES = {"choice", "noul", "score"}


def validate(sig):
    errors = []

    # Required top-level fields
    for field in REQUIRED_TOP_LEVEL:
        if field not in sig:
            errors.append(f"Missing required field: '{field}'")
    if errors:
        return errors

    if not isinstance(sig["model"], str) or not sig["model"]:
        errors.append("'model' must be a non-empty string")

    if not isinstance(sig["state_template"], dict):
        errors.append("'state_template' must be a JSON object")

    # Questions
    questions = sig.get("questions", {})
    if not isinstance(questions, dict) or not questions:
        errors.append("'questions' must be a non-empty JSON object")
    else:
        for qid, q in questions.items():
            if not isinstance(q, dict):
                errors.append(f"Question '{qid}' must be an object")
                continue
            qtype = q.get("type")
            if qtype not in VALID_QUESTION_TYPES:
                errors.append(
                    f"Question '{qid}': invalid type '{qtype}'. "
                    f"Must be one of: {', '.join(sorted(VALID_QUESTION_TYPES))}"
                )
                continue
            for field in ("type", "instructions"):
                if field not in q:
                    errors.append(f"Question '{qid}' (type={qtype}): missing required field '{field}'")

            # criteria required for choice and score; optional for noul (bare instructions are valid)
            if qtype in ("choice", "score") and "criteria" not in q:
                errors.append(f"Question '{qid}' (type={qtype}): missing required field 'criteria'")

            # instructions may be a string or a structured object (e.g. {question, today}); not null
            if "instructions" in q and q["instructions"] is None:
                errors.append(f"Question '{qid}': 'instructions' must not be null")

            # Noul: criteria must be object with exactly "true" and "false"
            if qtype == "noul" and "criteria" in q:
                c = q["criteria"]
                if not isinstance(c, dict):
                    errors.append(f"Question '{qid}': noul criteria must be a JSON object")
                else:
                    extra = set(c.keys()) - {"true", "false"}
                    missing = {"true", "false"} - set(c.keys())
                    if extra:
                        errors.append(f"Question '{qid}': noul criteria must only have 'true' and 'false' keys (unexpected: {sorted(extra)})")
                    if missing:
                        errors.append(f"Question '{qid}': noul criteria missing keys: {sorted(missing)}")

            # Score: criteria must be a list
            if qtype == "score" and "criteria" in q:
                if not isinstance(q["criteria"], list) or not q["criteria"]:
                    errors.append(f"Question '{qid}': score criteria must be a non-empty list of level descriptions")

    # Output template (optional)
    ot = sig.get("output_template")
    if ot is not None:
        if not isinstance(ot, dict):
            errors.append("'output_template' must be a JSON object")
        elif "columns" not in ot or not isinstance(ot["columns"], list):
            errors.append("'output_template' must have a 'columns' array")
        else:
            for i, col in enumerate(ot["columns"]):
                if not isinstance(col, dict):
                    errors.append(f"output_template.columns[{i}] must be an object")
                    continue
                if "header" not in col:
                    errors.append(f"output_template.columns[{i}]: missing 'header'")
                col_type = col.get("type", "path")
                if col_type == "confidence_flag":
                    if "path" not in col:
                        errors.append(f"output_template.columns[{i}] (confidence_flag): missing 'path'")
                elif "path" not in col:
                    errors.append(f"output_template.columns[{i}]: missing 'path'")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_signature.py <path/to/signature.sig.json>")
        sys.exit(1)

    sig_path = sys.argv[1]
    try:
        with open(sig_path, "r", encoding="utf-8") as f:
            sig = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {sig_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {sig_path}: {e}")
        sys.exit(1)

    errors = validate(sig)
    if errors:
        print(f"INVALID: {sig_path}")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        name = sig.get("name", "(unnamed)")
        q_count = len(sig.get("questions", {}))
        ot_count = len(sig.get("output_template", {}).get("columns", []))
        print(f"VALID: '{name}' — {q_count} question(s), {ot_count} output column(s)")
        sys.exit(0)


if __name__ == "__main__":
    main()
