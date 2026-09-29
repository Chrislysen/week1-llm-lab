"""lineage_e29r.py: E29-R corpus -- the E29-S 2x2 re-rendered in other list formats.

DECLARED in docs/protocols/E29R-formats.md before any decider call.

E29-S found that a stored rejection is ignored only when it is BOTH subordinate
to the record it rejects AND verb-less (`- [withdrawn] A proposed to X.`). That
was measured in one list format, markdown bullets. E29-R asks whether the
pattern is a fact about item structure or about markdown.

The four stores are E29-S's own (`store_s`), item for item and character for
character. Only the container changes:

    markdown   - A proposed to X.                 (E29-S, not re-run)
    json       {"notes": ["A proposed to X.", ...]}
    xml        <notes><note>A proposed to X.</note>...</notes>
    numbered   1. A proposed to X.

The header, the plan instruction, the pinned plan length and everything else in
the prompt are E29-S's. A test asserts that every rendering parses back to
exactly E29-S's items, and that the markdown rendering is byte-identical to the
block E29-S sent.
"""
import json
from xml.sax.saxutils import escape

from lineage_e29s import DESIGNS_S, store_s

FORMATS_R = ("markdown", "json", "xml", "numbered")
RUN_FORMATS = ("json", "xml", "numbered")          # markdown is E29-S's own data
HEADER = ("MEMORY NOTES FROM THE DISCUSSION\n"
          "-------------------------------\n")


def render(fmt, items):
    """One list of note strings, in one container format."""
    if fmt == "markdown":
        return "\n".join(f"- {x}" for x in items)
    if fmt == "json":
        return json.dumps({"notes": list(items)}, indent=2, ensure_ascii=False)
    if fmt == "xml":
        return "<notes>\n" + "\n".join(f"  <note>{escape(x)}</note>" for x in items) + "\n</notes>"
    if fmt == "numbered":
        return "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1))
    raise ValueError(fmt)


def context_block_r(fmt, design, instance, dialogue):
    items, _ = store_s(design, instance, dialogue)
    return HEADER + render(fmt, items)


__all__ = ["FORMATS_R", "RUN_FORMATS", "DESIGNS_S", "render", "context_block_r"]
