# QWQ evidence export — fixtures 0 and 1

For **independent semantic inspection**: does the complete delivered task unambiguously ask for what the scorer rewards? The earlier wiring audit answered a different question (whether the intended bytes reached the client), and does not bear on this one.

**Zero model calls were made to produce this export.** Nothing was modified, tuned or re-run.

## Provenance key

| label | meaning |
|---|---|
| **CAPTURED** | read verbatim from `results/qwq_calls.jsonl` |
| **RECONSTRUCTED** | rebuilt now from deterministic code; **not** logged at run time |

The message content sent to the model is CAPTURED. The JSON envelope around it was never logged, so it is RECONSTRUCTED from the runner's module constants.

## System instructions

**There is no system message.** RECONSTRUCTED from the runner, which builds `[{"role": "user", "content": prompt}]`. The entire task is one user message; the complete text of all eight is below.

## Response schema / format example (the only one given)

CAPTURED — this exact text is the tail of every message:

```
Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

## Fixture 0 — payments — INVARIANT: same label on all four assignments

**Option → sequence mapping** (RECONSTRUCTED; identical across all four assignments):

| label | sequence |
|---|---|
| P3 | SNAPSHOT_STORE → DRAIN_NODE → SHIFT_ROUTING → CYCLE_ENGINE |
| P1 | DRAIN_NODE → SNAPSHOT_STORE → CYCLE_ENGINE → SHIFT_ROUTING |
| P4 | DRAIN_NODE → SNAPSHOT_STORE → SHIFT_ROUTING → CYCLE_ENGINE |
| P2 | SNAPSHOT_STORE → DRAIN_NODE → CYCLE_ENGINE → SHIFT_ROUTING |

**Display order** (RECONSTRUCTED): P3, P1, P4, P2

**Action identifier → natural phrase** (RECONSTRUCTED; note that the prompt itself never states this mapping):

| identifier | phrase used in the fact messages |
|---|---|
| `DRAIN_NODE` | drain the failing node |
| `SNAPSHOT_STORE` | snapshot the store |
| `SHIFT_ROUTING` | shift routing to the spare region |
| `CYCLE_ENGINE` | cycle the settlement engine |

### Fixture 0, assignment 0

- process block (CAPTURED): `qwq:block0:payments`, position 2
- gold constraints (RECONSTRUCTED): **F1** DRAIN_NODE before SNAPSHOT_STORE; **F2** SHIFT_ROUTING before CYCLE_ENGINE
- correct label (RECONSTRUCTED): **P4**
- decoded choice (CAPTURED): **P4**
- executable score (CAPTURED): parsed=True, ready=True, violated=[], success=**True**
- done_reason=stop, truncated=False, thinking field=None, tokens 208+13, 2.324s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a payments platform degradation

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P3: SNAPSHOT_STORE -> DRAIN_NODE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P1: DRAIN_NODE -> SNAPSHOT_STORE -> CYCLE_ENGINE -> SHIFT_ROUTING
  P4: DRAIN_NODE -> SNAPSHOT_STORE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P2: SNAPSHOT_STORE -> DRAIN_NODE -> CYCLE_ENGINE -> SHIFT_ROUTING

Messages from your teammates:

Do not snapshot the store before we drain the failing node.

We cannot cycle the settlement engine until we shift routing to the spare region.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P4", "ready": true}
```

### Fixture 0, assignment 1

- process block (CAPTURED): `qwq:block0:payments`, position 3
- gold constraints (RECONSTRUCTED): **F1** DRAIN_NODE before SNAPSHOT_STORE; **F2** CYCLE_ENGINE before SHIFT_ROUTING
- correct label (RECONSTRUCTED): **P1**
- decoded choice (CAPTURED): **P4**
- executable score (CAPTURED): parsed=True, ready=True, violated=['F2'], success=**False**
- done_reason=stop, truncated=False, thinking field=None, tokens 208+13, 2.301s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a payments platform degradation

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P3: SNAPSHOT_STORE -> DRAIN_NODE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P1: DRAIN_NODE -> SNAPSHOT_STORE -> CYCLE_ENGINE -> SHIFT_ROUTING
  P4: DRAIN_NODE -> SNAPSHOT_STORE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P2: SNAPSHOT_STORE -> DRAIN_NODE -> CYCLE_ENGINE -> SHIFT_ROUTING

Messages from your teammates:

Do not snapshot the store before we drain the failing node.

We cannot shift routing to the spare region until we cycle the settlement engine.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P4", "ready": true}
```

### Fixture 0, assignment 2

- process block (CAPTURED): `qwq:block0:payments`, position 1
- gold constraints (RECONSTRUCTED): **F1** SNAPSHOT_STORE before DRAIN_NODE; **F2** SHIFT_ROUTING before CYCLE_ENGINE
- correct label (RECONSTRUCTED): **P3**
- decoded choice (CAPTURED): **P4**
- executable score (CAPTURED): parsed=True, ready=True, violated=['F1'], success=**False**
- done_reason=stop, truncated=False, thinking field=None, tokens 208+13, 12.687s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a payments platform degradation

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P3: SNAPSHOT_STORE -> DRAIN_NODE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P1: DRAIN_NODE -> SNAPSHOT_STORE -> CYCLE_ENGINE -> SHIFT_ROUTING
  P4: DRAIN_NODE -> SNAPSHOT_STORE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P2: SNAPSHOT_STORE -> DRAIN_NODE -> CYCLE_ENGINE -> SHIFT_ROUTING

Messages from your teammates:

Do not drain the failing node before we snapshot the store.

We cannot cycle the settlement engine until we shift routing to the spare region.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P4", "ready": true}
```

### Fixture 0, assignment 3

- process block (CAPTURED): `qwq:block0:payments`, position 4
- gold constraints (RECONSTRUCTED): **F1** SNAPSHOT_STORE before DRAIN_NODE; **F2** CYCLE_ENGINE before SHIFT_ROUTING
- correct label (RECONSTRUCTED): **P2**
- decoded choice (CAPTURED): **P4**
- executable score (CAPTURED): parsed=True, ready=True, violated=['F1', 'F2'], success=**False**
- done_reason=stop, truncated=False, thinking field=None, tokens 208+13, 2.3s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a payments platform degradation

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P3: SNAPSHOT_STORE -> DRAIN_NODE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P1: DRAIN_NODE -> SNAPSHOT_STORE -> CYCLE_ENGINE -> SHIFT_ROUTING
  P4: DRAIN_NODE -> SNAPSHOT_STORE -> SHIFT_ROUTING -> CYCLE_ENGINE
  P2: SNAPSHOT_STORE -> DRAIN_NODE -> CYCLE_ENGINE -> SHIFT_ROUTING

Messages from your teammates:

Do not drain the failing node before we snapshot the store.

We cannot shift routing to the spare region until we cycle the settlement engine.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P4", "ready": true}
```

## Fixture 1 — robotics — VARYING: label changed across assignments

**Option → sequence mapping** (RECONSTRUCTED; identical across all four assignments):

| label | sequence |
|---|---|
| P1 | LOCK_BAY → HALT_CONVEYOR → CALIBRATE_ARM → SWAP_GRIPPER |
| P4 | HALT_CONVEYOR → LOCK_BAY → SWAP_GRIPPER → CALIBRATE_ARM |
| P2 | HALT_CONVEYOR → LOCK_BAY → CALIBRATE_ARM → SWAP_GRIPPER |
| P3 | LOCK_BAY → HALT_CONVEYOR → SWAP_GRIPPER → CALIBRATE_ARM |

**Display order** (RECONSTRUCTED): P1, P4, P2, P3

**Action identifier → natural phrase** (RECONSTRUCTED; note that the prompt itself never states this mapping):

| identifier | phrase used in the fact messages |
|---|---|
| `HALT_CONVEYOR` | halt the conveyor |
| `LOCK_BAY` | lock the loading bay |
| `CALIBRATE_ARM` | calibrate the picker arm |
| `SWAP_GRIPPER` | swap the gripper assembly |

### Fixture 1, assignment 0

- process block (CAPTURED): `qwq:block1:robotics`, position 2
- gold constraints (RECONSTRUCTED): **F1** HALT_CONVEYOR before LOCK_BAY; **F2** CALIBRATE_ARM before SWAP_GRIPPER
- correct label (RECONSTRUCTED): **P2**
- decoded choice (CAPTURED): **P2**
- executable score (CAPTURED): parsed=True, ready=True, violated=[], success=**True**
- done_reason=stop, truncated=False, thinking field=None, tokens 232+13, 2.291s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a warehouse robotics fault

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P1: LOCK_BAY -> HALT_CONVEYOR -> CALIBRATE_ARM -> SWAP_GRIPPER
  P4: HALT_CONVEYOR -> LOCK_BAY -> SWAP_GRIPPER -> CALIBRATE_ARM
  P2: HALT_CONVEYOR -> LOCK_BAY -> CALIBRATE_ARM -> SWAP_GRIPPER
  P3: LOCK_BAY -> HALT_CONVEYOR -> SWAP_GRIPPER -> CALIBRATE_ARM

Messages from your teammates:

Do not lock the loading bay before we halt the conveyor.

We cannot swap the gripper assembly until we calibrate the picker arm.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P2", "ready": true}
```

### Fixture 1, assignment 1

- process block (CAPTURED): `qwq:block1:robotics`, position 4
- gold constraints (RECONSTRUCTED): **F1** HALT_CONVEYOR before LOCK_BAY; **F2** SWAP_GRIPPER before CALIBRATE_ARM
- correct label (RECONSTRUCTED): **P4**
- decoded choice (CAPTURED): **P4**
- executable score (CAPTURED): parsed=True, ready=True, violated=[], success=**True**
- done_reason=stop, truncated=False, thinking field=None, tokens 232+13, 2.295s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a warehouse robotics fault

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P1: LOCK_BAY -> HALT_CONVEYOR -> CALIBRATE_ARM -> SWAP_GRIPPER
  P4: HALT_CONVEYOR -> LOCK_BAY -> SWAP_GRIPPER -> CALIBRATE_ARM
  P2: HALT_CONVEYOR -> LOCK_BAY -> CALIBRATE_ARM -> SWAP_GRIPPER
  P3: LOCK_BAY -> HALT_CONVEYOR -> SWAP_GRIPPER -> CALIBRATE_ARM

Messages from your teammates:

Do not lock the loading bay before we halt the conveyor.

We cannot calibrate the picker arm until we swap the gripper assembly.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P4", "ready": true}
```

### Fixture 1, assignment 2

- process block (CAPTURED): `qwq:block1:robotics`, position 3
- gold constraints (RECONSTRUCTED): **F1** LOCK_BAY before HALT_CONVEYOR; **F2** CALIBRATE_ARM before SWAP_GRIPPER
- correct label (RECONSTRUCTED): **P1**
- decoded choice (CAPTURED): **P2**
- executable score (CAPTURED): parsed=True, ready=True, violated=['F1'], success=**False**
- done_reason=stop, truncated=False, thinking field=None, tokens 232+13, 2.3s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a warehouse robotics fault

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P1: LOCK_BAY -> HALT_CONVEYOR -> CALIBRATE_ARM -> SWAP_GRIPPER
  P4: HALT_CONVEYOR -> LOCK_BAY -> SWAP_GRIPPER -> CALIBRATE_ARM
  P2: HALT_CONVEYOR -> LOCK_BAY -> CALIBRATE_ARM -> SWAP_GRIPPER
  P3: LOCK_BAY -> HALT_CONVEYOR -> SWAP_GRIPPER -> CALIBRATE_ARM

Messages from your teammates:

Do not halt the conveyor before we lock the loading bay.

We cannot swap the gripper assembly until we calibrate the picker arm.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P2", "ready": true}
```

### Fixture 1, assignment 3

- process block (CAPTURED): `qwq:block1:robotics`, position 1
- gold constraints (RECONSTRUCTED): **F1** LOCK_BAY before HALT_CONVEYOR; **F2** SWAP_GRIPPER before CALIBRATE_ARM
- correct label (RECONSTRUCTED): **P3**
- decoded choice (CAPTURED): **P4**
- executable score (CAPTURED): parsed=True, ready=True, violated=['F1'], success=**False**
- done_reason=stop, truncated=False, thinking field=None, tokens 232+13, 2.418s

**Request envelope — RECONSTRUCTED** (the envelope was not logged; `messages[0].content` below is CAPTURED and shown in full after it):

```json
{
  "model": "qwen3:14b",
  "messages": [
    {
      "role": "user",
      "content": "<< CAPTURED, reproduced verbatim below >>"
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "seed": 0,
    "num_predict": 300
  }
}
```

**Message content — CAPTURED, exact text:**

```
Setting: a warehouse robotics fault

What you already know:
- (nothing beyond the plans below)

Candidate plans:
  P1: LOCK_BAY -> HALT_CONVEYOR -> CALIBRATE_ARM -> SWAP_GRIPPER
  P4: HALT_CONVEYOR -> LOCK_BAY -> SWAP_GRIPPER -> CALIBRATE_ARM
  P2: HALT_CONVEYOR -> LOCK_BAY -> CALIBRATE_ARM -> SWAP_GRIPPER
  P3: LOCK_BAY -> HALT_CONVEYOR -> SWAP_GRIPPER -> CALIBRATE_ARM

Messages from your teammates:

Do not halt the conveyor before we lock the loading bay.

We cannot calibrate the picker arm until we swap the gripper assembly.

Choose the one candidate plan that respects everything you know.

Answer as JSON and nothing else: {"option": "P?", "ready": true}

`option` is the identifier of the plan you choose.
`ready` is true if you consider that plan safe to execute as written.
```

**Raw response — CAPTURED, exact text:**

```
{"option": "P4", "ready": true}
```

## For the reviewer

The question is whether the delivered task unambiguously asks for what the scorer rewards. Two features are surfaced without interpretation:

1. The fact messages refer to actions by **natural-language phrase** ("snapshot the store"); the candidate plans list them by **identifier** (`SNAPSHOT_STORE`). The prompt **never states the mapping** between the two. It is recoverable by inference, and no claim is made here about whether that inference is reliable.
2. Success additionally requires `ready=true`; a correct option chosen with `ready=false` scores as failure. In these 32 calls `ready` was true every time, so this did not bind — it is listed because it is part of what the scorer rewards.

No recommendation for a further experiment is made in this document.