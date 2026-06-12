"""
main.py — Entry point for the Carbon Footprint Assistant.

Run with:
    python main.py

Type 'help' for a full list of commands.  Type 'exit' or 'quit' to leave.
"""

from __future__ import annotations

import sys

from assistant import CarbonAssistant, HELP_TEXT

BANNER = """
  ╔═══════════════════════════════════════════════════╗
  ║   🌍  Carbon Footprint Assistant  v1.0            ║
  ║   Track your emissions.  Make better choices.     ║
  ╚═══════════════════════════════════════════════════╝
  Type 'help' to see available commands.
  Type 'exit' or 'quit' to close the assistant.
"""

EXIT_COMMANDS = {"exit", "quit"}
HELP_COMMANDS = {"help", "--help", "-h"}


def run() -> None:
    """Start the interactive command-line loop."""
    print(BANNER)

    assistant = CarbonAssistant()

    while True:
        try:
            raw = input("You ▶  ").strip()
        except (EOFError, KeyboardInterrupt):
            # Graceful exit on Ctrl-D / Ctrl-C
            print("\n\n  👋  Goodbye! Keep making greener choices.\n")
            sys.exit(0)

        if not raw:
            continue

        lower = raw.lower()

        if lower in EXIT_COMMANDS:
            print("\n  👋  Goodbye! Keep making greener choices.\n")
            sys.exit(0)

        if lower in HELP_COMMANDS:
            print(HELP_TEXT)
            continue

        response = assistant.process(raw)
        print(f"\n{response}\n")


if __name__ == "__main__":
    run()