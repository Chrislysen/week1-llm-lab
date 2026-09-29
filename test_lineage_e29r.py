"""Zero-model-call checks for E29-R: only the list container may change."""
import json
import re
from xml.etree import ElementTree

from lineage_e29 import all_e29_dialogues
from lineage_e29r import FORMATS_R, HEADER, RUN_FORMATS, context_block_r, render
from lineage_e29s import DESIGNS_S, context_block_s, store_s

DS = all_e29_dialogues()
ARMS = ("restated", "neutral")


def parse_back(fmt, body):
    """Recover the note strings from one rendered container."""
    if fmt == "markdown":
        return [ln[2:] for ln in body.split("\n")]
    if fmt == "json":
        return json.loads(body)["notes"]
    if fmt == "xml":
        return [n.text for n in ElementTree.fromstring(body).findall("note")]
    if fmt == "numbered":
        return [re.sub(r"^\d+\. ", "", ln) for ln in body.split("\n")]
    raise ValueError(fmt)


def test_markdown_is_byte_identical_to_e29s():
    """The markdown column is E29-S's data, so its prompt must be E29-S's prompt."""
    for d in DS:
        for arm in ARMS:
            for X in DESIGNS_S:
                assert context_block_r("markdown", X, d["instance"], d["arms"][arm]) == \
                    context_block_s(X, d["instance"], d["arms"][arm]), (X, d["instance"].id, arm)


def test_every_format_carries_exactly_the_e29s_items():
    """Same items, same order, same characters: only the container differs."""
    for d in DS:
        for arm in ARMS:
            for X in DESIGNS_S:
                items, _ = store_s(X, d["instance"], d["arms"][arm])
                for fmt in FORMATS_R:
                    block = context_block_r(fmt, X, d["instance"], d["arms"][arm])
                    assert block.startswith(HEADER)
                    assert parse_back(fmt, block[len(HEADER):]) == items, (fmt, X, d["instance"].id, arm)


def test_merged_has_one_item_fewer_in_every_format():
    for d in DS:
        a, _ = store_s("addonly", d["instance"], d["arms"]["neutral"])
        m, _ = store_s("addonly_merged", d["instance"], d["arms"]["neutral"])
        for fmt in FORMATS_R:
            assert len(parse_back(fmt, render(fmt, m))) == len(parse_back(fmt, render(fmt, a))) - 1


def test_run_formats_exclude_markdown():
    assert "markdown" not in RUN_FORMATS and set(RUN_FORMATS) < set(FORMATS_R)


def test_xml_escaping_round_trips():
    tricky = ["A & B proposed <x> to \"y\"; it's fine."]
    assert parse_back("xml", render("xml", tricky)) == tricky


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
