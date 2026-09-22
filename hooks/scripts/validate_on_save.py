"""
PostToolUse hook: auto-validates .sig.json files when written.

Reads the tool event from stdin as JSON. If a .sig.json file was just written,
runs validate_signature.py and prints the result to the Claude Code console.
"""

import json
import os
import subprocess
import sys


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Only act on Write tool completions
    if event.get("tool_name") != "Write":
        sys.exit(0)

    file_path = event.get("tool_input", {}).get("file_path", "")
    if not file_path.endswith(".sig.json"):
        sys.exit(0)

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    validator   = os.path.join(plugin_root, "scripts", "validate_signature.py")

    if not os.path.isfile(validator):
        # Plugin not fully installed — skip silently
        sys.exit(0)

    result = subprocess.run(
        [sys.executable, validator, file_path],
        capture_output=True,
        text=True,
    )

    output = (result.stdout or result.stderr).strip()
    if output:
        status = "✓" if result.returncode == 0 else "✗"
        print(f"[typesafe-jev] {status} {output}")


if __name__ == "__main__":
    main()
