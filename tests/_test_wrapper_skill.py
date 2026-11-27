"""WRAPPER-SKILL.md stands alone and stays honest.

The file is pasted into a chat as a raw GitHub URL, so it must not point at anything private, must
name the commands a wrapper author runs, and must keep each shell block to one command.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "WRAPPER-SKILL.md"

REQUIRED = [
    "crab wrappers new",
    "--local",
    "crab wrappers test",
    "--strict",
    "crab receipts set",
    "crab wrappers list",
    "read_data",
    "expected.json",
]
FORBIDDEN = [
    ".crab-web-dev",
    ".claude",
    "ADR-",
    "../CRAB",
    "/home/",
    "Claude",
    "subagent",
    "GPT",
    "Gemini",
    "Sonnet",
    "Opus",
]
SHELL_LANGUAGES = {"", "bash", "sh", "console", "shell"}


def _text() -> str:
    return SKILL.read_text()


def _fenced_blocks(text: str) -> list[tuple[str, str]]:
    """(language, body) of every fenced block."""
    return re.findall(r"^```(\w*)\n(.*?)^```$", text, flags=re.S | re.M)


def _commands(body: str) -> list[str]:
    """The commands in a shell block: a line ending in a backslash continues its command."""
    commands: list[str] = []
    continuing = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if continuing:
            commands[-1] += " " + stripped
        else:
            commands.append(stripped)
        continuing = stripped.endswith("\\")
    return commands


def test_skill_exists_at_the_repository_root():
    assert SKILL.is_file()


def test_skill_names_the_commands_and_files_an_author_needs():
    text = _text()
    assert [item for item in REQUIRED if item not in text] == []


def test_skill_names_nothing_private_and_no_model_or_tool():
    text = _text()
    assert [item for item in FORBIDDEN if item in text] == []
    assert "—" not in text


def test_every_shell_block_holds_exactly_one_command():
    blocks = _fenced_blocks(_text())
    assert blocks, "the skill has no fenced blocks"
    bad = []
    for language, body in blocks:
        if language in SHELL_LANGUAGES and len(_commands(body)) != 1:
            bad.append(body.strip())
    assert bad == []
