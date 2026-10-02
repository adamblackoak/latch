# When does an AI judgement become usable?

Adam Searle · Black Oak Projects · 2 October 2026

**The confidence stays at 97%. The permission to rely changes.**

A generated judgement recommends escalating an account for enhanced review. Latch initially refuses reliance. An explicit adoption makes that judgement usable for case routing. A request for a different scope is refused. Two challenges suspend new reliance; resolving only one does not restore it. Resolving both permits a second receipt. Withdrawal stops further reliance.

This walkthrough runs the existing Latch Python engine. The case, confidence value, actors and review decisions are synthetic inputs. No model inference, account routing or customer contact takes place.

## See the result

Fresh local execution on 2 October 2026 produced:

| Attempt | Result | New reliance receipts |
| --- | --- | ---: |
| Candidate at 97% confidence, without adoption | REFUSED | 0 |
| Adoption submitted with `adopter_kind="model"` | REFUSED | 0 |
| Reliance after explicit adoption for case routing | ALLOWED | 1 |
| Attempt to use that adoption for customer contact | REFUSED | 0 |
| Reliance with two open challenges | REFUSED | 0 |
| Reliance after resolving only one challenge | REFUSED | 0 |
| Reliance after resolving both challenges by reaffirmation | ALLOWED | 1 |
| Reliance after withdrawal | REFUSED | 0 |

**Eight expected outcomes, two reliance receipts, ten ledger events.** The internal hash chain verified. Earlier receipts remain recorded after challenge and withdrawal; the boundary governs new reliance and does not reverse past effects.

[Inspect the actual results](evidence/standing-2026-10-02/result.json) · [Inspect the ledger](evidence/standing-2026-10-02/ledger.jsonl)

## Run it

From a repository checkout, with Python 3.11 or later:

```bash
python examples/standing_walkthrough.py
```

No additional packages are needed for this command. It prints the eight outcomes and saves a new timestamped folder under `.demo/` containing `result.json` and `ledger.jsonl`. The script refuses to overwrite an existing output directory. Receipt IDs and timestamps vary between runs.

The [walkthrough driver](../examples/standing_walkthrough.py) uses the unchanged engine from [the 22 September implementation](https://github.com/adamblackoak/latch/commit/2711ad534fcb0f60b5080aa875d579c424504d6a). The retained result records the source hashes and execution environment. The existing 15-test suite also passed locally on Python 3.12. These are local execution results, not an external certification.

## What changes at the boundary

Adoption records an actor, an authority reference, a scope and a basis. A successful reliance call produces a receipt linked to that adoption. A challenge changes eligibility without changing the candidate's confidence. The caller can inspect both the judgement and the history of its use.

This is a concrete distinction between retaining an assessment and permitting a particular use of it. It also leaves room for a judgement to remain useful within one scope while being unavailable for another.

## Read alongside current research

[AuthorityLens](https://arxiv.org/abs/2609.32378v1), by Shaojin Chen and colleagues, measures authority through outcomes and the minimal combinations of participants sufficient to realise them. It motivates a demanding question for a governance demonstration: does a claimed prerequisite change what can actually happen?

Here the measured outcome is a reliance receipt through Latch's normal API. The walkthrough shows adoption, scope and challenge checks affecting that outcome. It does **not** establish a multi-principal authority-separation score: actor kinds and authority references are caller-supplied, and the same local process can supply all of them. Authenticated identities, protected execution routes and exhaustive bypass analysis would be separate work. This is a related worked example, not a reproduction of the AuthorityLens evaluation.

[Evaluating System One Models for Agent Security Decisions](https://arxiv.org/abs/2609.33401v2), by Yixuan Liu, finds that favourable aggregate results can coexist with concentrated high-confidence mistakes. That provides context for separating prediction confidence from permission to rely. Latch does not detect those mistakes or make an adopted judgement correct; it makes the standing of a judgement explicit and challengeable.

[Contract monitoring: governing AI via separation of powers](https://arxiv.org/abs/2609.32061v1), by Enric Boix-Adsera, separates a monitor's evidenced violation report from its adjudication. Latch's challenge and resolution objects offer a point of comparison, but they do not implement that monitoring framework or validate the substance of a challenge.

These papers do not evaluate or endorse Latch. The comparison above is this project's interpretation of their relevance.

## Exact scope

The result is a local adoption-and-reliance demonstration. It establishes the observed API outcomes and retained receipts. It does not establish production authentication, external action enforcement, model quality, legal compliance or trusted external custody. Refusals are captured by the walkthrough driver; the engine does not append them as refusal events. A hash chain establishes internal consistency, not non-repudiation.

## Request a walkthrough

If you would like to see this existing demonstration walked through, [request a walkthrough](https://github.com/adamblackoak/latch/issues/new?template=walkthrough.md). You can indicate which part interests you: adoption, scope, challenge, or the evidence trail. Requests through this link are public GitHub issues.
