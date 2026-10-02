# Latch

**An adoption and reliance boundary for AI-generated judgement.**

A model output can be accurate, evidence-backed and 99% confident and still have no operational standing.

Latch makes that distinction executable.

**Start with the worked example:** [When does an AI judgement become usable?](docs/WHEN_JUDGEMENT_BECOMES_USABLE.md) — eight observed outcomes, retained evidence and a one-command walkthrough. [Request a walkthrough of the existing demo](https://github.com/adamblackoak/latch/issues/new?template=walkthrough.md).

```text
model output
   |
   v
CANDIDATE JUDGEMENT
   |        confidence is metadata, not authority
   v
EXPLICIT ADOPTION  <---- authority + scope + basis
   |
   v
ELIGIBLE FOR RELIANCE
   |
   +---- challenge raised ----> CONTESTED ----> reliance suspended
   |                                  |
   |                           reaffirm / withdraw
   v
RELIANCE RECEIPT
```

## The invariant

> **Generation is not adoption. Adoption is not reliance. Confidence is not authority.**

Latch refuses to let a generated judgement silently become an operational fact just because it appears in a workflow, carries a high confidence score, or dresses itself up as approval.

An output remains a **candidate judgement** until an authorised actor explicitly adopts it for a defined scope and records the basis for doing so. A downstream actor can rely on it only inside that adopted scope. If the judgement is challenged, further reliance is suspended until every open challenge has been resolved.

That is a small boundary. It has large consequences.

## Run the proof

Python 3.11+.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
latch demo --ledger .demo/latch.jsonl
python -m unittest discover -s tests -v
latch verify .demo/latch.jsonl
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -e .
latch demo --ledger .demo/latch.jsonl
python -m unittest discover -s tests -v
latch verify .demo/latch.jsonl
```

The demo proves all of these paths using the real boundary code:

- `0.97` model confidence does **not** permit reliance.
- a model cannot self-adopt its own judgement.
- adoption requires an explicit authority reference, scope and basis.
- an adopted judgement can be relied on inside that scope.
- a scope mismatch is refused.
- a challenge immediately suspends new reliance.
- a review that reaffirms the adopted judgement restores eligibility only when no other challenges remain open.
- every accepted reliance produces a receipt linked to the adoption.
- the event ledger is hash-chained and independently verifiable.

## Why this exists

A lot of AI governance stops at the model boundary: evaluation, confidence, explainability, prompt controls, approval screens.

But the consequential question arrives later:

**When did this output acquire enough standing for somebody or something to act as though it were true?**

Latch calls that transition **adoption**, then records the separate moment of **reliance**.

This matters because a human-in-the-loop is not automatically a control. A human who merely sees, forwards or clicks past an output has not necessarily adopted responsibility for it. Conversely, an explicit adoption can be narrow: a judgement may be accepted for one purpose without becoming a free-floating fact for every downstream use.

## What is actually implemented

This repository contains executable code, not only a conceptual schema:

- candidate judgement registration
- explicit adoption with actor, authority reference, scope and basis references
- refusal of model self-adoption
- scope-bound reliance
- reliance receipts
- challenge and challenge resolution
- automatic suspension of reliance while contested
- withdrawal of an adopted judgement
- append-only JSONL event recording
- SHA-256 hash-chain verification
- invariant tests

## Deliberate limits

Latch is a reference implementation and governance specimen, not a production control plane.

It does **not** claim:

- that human adoption makes a judgement correct
- legal or regulatory compliance
- production identity or authorisation
- cryptographic signatures or non-repudiation
- distributed tamper resistance
- model-quality evaluation
- automatic truth determination
- integration with private Black Oak systems

The hash chain is evidence of internal sequence integrity, not a substitute for trusted custody or external attestation.

## Relationship to agentic control

Latch governs a different transition from an execution firewall.

An execution control asks:

> Is this action authorised to happen?

Latch asks one step earlier:

> **What judgement is this action relying on, and when did that judgement acquire operational standing?**

The two boundaries can be composed, but this repository deliberately does not integrate them.

## Public thesis

AI outputs should remain candidate judgement until adopted by a governed process. Reliance is the point where an output becomes operationally consequential, so reliance should be attributable, scoped, challengeable and inspectable.

See [`docs/BOUNDARY.md`](docs/BOUNDARY.md) for the compact boundary note.

## License

MIT.
