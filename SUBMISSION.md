# Submission index

KIUA2003/KIUA2005 AgentCom compulsory. Start with the report.

| document | what it is |
|---|---|
| [docs/REPORT.md](docs/REPORT.md) | **the report** |
| [docs/DEMO.md](docs/DEMO.md) | demo commands, code walk-through, likely questions |
| [docs/design.md](docs/design.md) | scenario, personas and system prompts, success criterion |
| [docs/FAILURE-ANALYSIS.md](docs/FAILURE-ANALYSIS.md) | intentional failure analysis (15 cases) |
| [docs/COMP-ANALYSIS.md](docs/COMP-ANALYSIS.md) | detailed analysis of the 12 frozen runs |
| [docs/SUPPLEMENTARY-T07.md](docs/SUPPLEMENTARY-T07.md) | supplementary run: declaration, then results |

The experiment evidence (`transcripts/exp/`, `results/*.csv`) is frozen at tag
`compulsory-baseline-v1` and was not modified afterwards; every later file is an
addition. Research beyond the compulsory is on branch `crazy`.

Quick check: `for t in test_*.py; do python $t; done` and
`python failure_analysis.py --offline` (no model needed).
