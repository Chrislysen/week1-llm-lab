export const meta = {
  name: 'attack-e13',
  description: 'Adversarial panel attacking whatever E13 concludes',
  phases: [
    { title: 'Attack', detail: 'five lenses hunting for a confound or an overclaim' },
    { title: 'Refute', detail: 'each candidate handed to a skeptic' },
  ],
}

const REPO = 'C:/Users/chris/week1-llm-lab'

const CONTEXT = `
You are auditing a research repo at ${REPO}. Read the actual files; do not
speculate about code you have not opened. Compute from the CSVs where useful.

KEY FILES: docs/protocols/E13-recognition-utilization-v1.md, lineage_e13.py,
e13_recognition.py, test_lineage_e13.py, prospective_design_check.py,
results/e13_*.csv, results/e13_*.json, and for background
docs/protocols/E10-H3-RETRACTION.md and docs/findings.md.

BACKGROUND. E12 established (108 units in 36 instance clusters, cluster
permutation + cluster bootstrap) that this model prices k corroborating reports
tracing to ONE evidential root the same as k INDEPENDENT roots: difference
+0.0185, p = 0.749, 95% CI [-0.037, +0.074], inside a preregistered SESOI of
0.10. A separate frozen probe shows the model CAN report the difference (27/36
vs 0/36, p = 1.5e-08).

E13 asks whether routing that recognition into the reasoning step changes the
decision. Five interventions x two dependence levels x 108 units:
  default (byte-identical to E12's prompt), identify (must state the evidence
  structure first), normative (identify + a frozen principle), sham (matched
  structured-output burden about a task-IRRELEVANT property), gold (correct
  structure stated outright; diagnostic only, never pooled).

THIS PROJECT HAS ALREADY RETRACTED ONE CONCLUSION for reporting a null that its
own preregistered code called inconclusive. Read
docs/protocols/E10-H3-RETRACTION.md so you do not re-find that; find the NEXT
one.

YOUR JOB: show that whatever E13 concludes is WRONG, UNSUPPORTED, or an
artifact. Cite file:line or specific data. Vague concerns are worthless.
Do NOT run any model (no ollama). Do NOT propose fixes.
`

const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          mechanism: { type: 'string' },
          evidence: { type: 'string' },
          severity: { type: 'string', enum: ['fatal', 'serious', 'minor'] },
        },
        required: ['title', 'file', 'mechanism', 'evidence', 'severity'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    survives: { type: 'boolean' },
    reasoning: { type: 'string' },
    correction: { type: 'string' },
  },
  required: ['survives', 'reasoning'],
}

const LENSES = [
  { key: 'overclaim', prompt: `Lens: DOES THE WRITE-UP EXCEED ITS OWN DECISION PROCEDURE? This is the exact failure that produced the E10 retraction. Run \`python e13_recognition.py --analyse\` yourself and compare EVERY sentence of what it prints, and of the latest commit message, against the preregistered rules in the protocol (SESOI, the powered discordance band [0.08,0.12], the INCONCLUSIVE-BY-RULE contingency, Holm correction, diagnostic arms never pooled). Quote any place the reported conclusion is stronger than the rule permits.` },
  { key: 'parse', prompt: `Lens: PARSE-RATE CONFOUND. The intervention arms demand a four-key JSON from a 3B model; default demands two keys. Read results/e13_*.csv and compute parse rate per (intervention, dependence). Is there a differential parse failure between arms, or between the two dependence levels WITHIN an arm? Does the completeness filter in _by_unit fully neutralise it, or does selective survival still bias the flip rates? Check dropped_incomplete counts.` },
  { key: 'recognition', prompt: `Lens: IS THE RECOGNITION MEASURE MEANINGFUL? Read recognition_correct() and the identify/normative instructions in lineage_e13.py. Does answering "same_underlying_source" actually demonstrate the model represents EVIDENTIAL DEPENDENCE, or could it be surface string-matching on whether the same basis phrase repeats? A model that notices "the platform spec" appears three times has done lexical matching, not evidential reasoning. If so, what does the coupling analysis actually show?` },
  { key: 'coupling', prompt: `Lens: THE COUPLING STATISTIC. Read the coupling block at the end of analyse(). P(sensitive|recognized) vs P(sensitive|misrecognized) is computed on subsets selected BY the model's own recognition, which is not randomly assigned. Is this comparison confounded by unit difficulty -- easy units may be both easier to recognise and easier to act correctly on? Are the subgroup sizes large enough to compare at all? Is any significance claimed for it?` },
  { key: 'sham', prompt: `Lens: IS SHAM A VALID CONTROL? Read the _SHAM and _ASSESS instruction strings. They are matched to within 1 word, but is SHAM equally DIFFICULT? "count the words in the longest message" may be far harder or far easier for a 3B model than judging shared sourcing, and a control that is not difficulty-matched cannot isolate the output burden. Check SHAM's own answers in the CSV for plausibility. Also: does GOLD's prompt differ structurally from DEFAULT in a way that makes its diagnostic reading unsafe?` },
]

phase('Attack')
const results = await pipeline(
  LENSES,
  l => agent(`${CONTEXT}\n\n${l.prompt}`, { label: `attack:${l.key}`, phase: 'Attack', schema: FINDING_SCHEMA }),
  (res, lens) => {
    const fs = (res && res.findings ? res.findings : []).filter(f => f.severity !== 'minor')
    return parallel(fs.map(f => () =>
      agent(`${CONTEXT}\n\nAn auditor claims the following. YOUR JOB IS TO REFUTE IT. Open the files and check. Default to survives=false if the claim is vague, is already stated as a limitation in the protocol or commit message, or does not actually undermine the specific conclusion E13 draws.\n\nTITLE: ${f.title}\nFILE: ${f.file}\nMECHANISM: ${f.mechanism}\nEVIDENCE: ${f.evidence}`,
        { label: `refute:${lens.key}`, phase: 'Refute', schema: VERDICT_SCHEMA })
        .then(v => ({ lens: lens.key, ...f, verdict: v }))
    ))
  }
)

const all = results.flat().filter(Boolean)
const confirmed = all.filter(f => f.verdict && f.verdict.survives)
log(`${all.length} candidates, ${confirmed.length} survived refutation`)
return {
  confirmed: confirmed.map(f => ({ lens: f.lens, severity: f.severity, title: f.title, mechanism: f.mechanism, evidence: f.evidence, why: f.verdict.reasoning })),
  refuted: all.filter(f => !(f.verdict && f.verdict.survives)).map(f => ({ title: f.title, why_refuted: (f.verdict && f.verdict.correction) || (f.verdict && f.verdict.reasoning) })),
}
