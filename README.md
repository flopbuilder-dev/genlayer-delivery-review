# DeliveryReview

An experimental GenLayer contract for recording a review of one text deliverable against requirements fixed at deployment. It is intended as a reusable component for agent task marketplaces and quality-review workflows. It does not hold funds, implement escrow, execute submitted code, or replace a legal adjudication process.

**Status:** initial implementation prepared with AI assistance. The package has 55 passing SDK direct-mode tests and a live Studio happy-path test. Read `validation/REPORT.md` for the evidence and remaining checks. Portal acceptance, rewards and airdrop eligibility remain unestablished.

## What the contract does

The requester deploys a record with a separate worker address and one to eight requirements. The assigned worker submits the complete deliverable once. Either participant can request an assessment; unrelated accounts cannot trigger inference. Requirements and the submitted text have no edit method. Cancellation is available to the requester only before submission.

The leader proposes a decision for each requirement. Each validator independently repeats the assessment using the same frozen requirements and delivered text. The validator compares stable fields: requirement ID, status and basis. It does not accept a result merely because its JSON looks correct. Supporting quotations may differ, but each must be an exact excerpt of the delivered text. A response containing fabricated quotations or missing/extra requirement IDs is rejected.

| Status | Basis | Evidence rule |
| --- | --- | --- |
| `met` | `supported` | Nonempty exact quotation |
| `unmet` | `contradicted` | Nonempty exact quotation |
| `unmet` | `missing` | Empty quotation; only for required content absent from this complete text |
| `insufficient_evidence` | `unverifiable` | Empty quotation; external facts, runtime behavior or ambiguous requirements |

The contract derives the aggregate result: any unmet criterion means `unmet`; otherwise any unverifiable criterion means `insufficient_evidence`; otherwise the aggregate is `met`. The accepted per-criterion results remain available for inspection. A recorded assessment closes further application-level assessment attempts on that record, including for an insufficient-evidence outcome. A materially revised deliverable needs a new record. GenLayer's own consensus retries and appeals are separate protocol operations.

## Run the local checks

Validated on Linux with Python 3.12. Windows execution has not been qualified. Use a new virtual environment:

```sh
python -m venv .venv
# Activate .venv using the command appropriate for your shell.
python -m pip install -r requirements-lock.txt
python tools/bootstrap_sdk.py
python -m pytest -q --junitxml=validation/pytest.xml
genvm-lint check contracts/delivery_review.py --json
```

The bootstrap script downloads a checksummed official GenVM release into the testing tools' caches. It works around a renamed release asset in the pinned test package; it does not modify installed package code. The SDK download is approximately 135 MB. Direct-mode tests then run without a wallet, API key, hosted model calls, or testnet balance. Network access is needed to install the tools and retrieve the SDK initially.

## Example inputs

Deploy using a separate test worker address and this requirements JSON:

```json
[
  {"id":"install","requirement":"Include a concrete installation command in the delivered text."},
  {"id":"execute","requirement":"Include a concrete command for running the program."}
]
```

From the worker account, call `submit_delivery` with:

```text
Install: pip install demo. Run: python demo.py.
```

From either participant, call `assess_delivery`, then inspect `get_record`. This example is synthetic; a `met` result says the requested commands occur in the text. It does not establish that `demo` exists, is safe, installs successfully or runs correctly. A requirement asking whether tests actually ran should yield `insufficient_evidence` from this text-only evidence model.

Use a disposable Studio account for a future smoke test. Deployment requires matching the contract's pinned SDK with the chosen network. Studio, Bradbury and other environments have distinct balances and configuration. A successful local test is not proof of a successful deployment.

The initial smoke test is now available at this [public Studio contract](https://explorer-studio.genlayer.com/address/0xD5C585E0f82ad85E7BCcb4401ABB4Ede807dc67b). The explorer's **Contract → Code** tab exposes the deployed source; the Transactions tab shows the three finalized successful operations. The test used separate disposable requester and worker accounts. It is not linked to the user's Portal wallet.

## Limits and threat model

- Submitted requirements, deliverable text and assessment are public contract data. Do not submit private customer data or secrets.
- Source quotations establish provenance within the supplied text, not truth. A worker can submit false statements; the contract does not fetch external corroboration.
- Prompt injection and correlated model errors remain possible. The fixed policy and JSON framing express the intended trust boundary but are not a proof that models will respect it.
- Validators may disagree on ambiguous requirements or the difference between absence and unverifiability. The implementation prefers a blocked/undetermined operation to deliberately weakening the comparison rule. Actual network liveness must be measured.
- Direct mode executes the leader first and lets a test invoke a captured validator separately. Its in-process state after the leader runs is not a simulation of network finality or rollback after failed consensus.
- Application state `assessment_recorded` does not mean the underlying transaction is FINALIZED. Consumers must check the protocol transaction status and appeal/finality conditions.
- The requester can cancel an open record; the worker can withhold submission. This component has no deadline, payment, dispute escalation or economic incentive mechanism.
- Input bounds are 8 criteria, 600 characters per requirement, 8,192 specification bytes, 24,576 deliverable bytes, 400 characters per quotation and 12,288 accepted model-output bytes. These are application limits, not a measured fee or execution-time guarantee.

## Why GenLayer is used

Semantic requirements cannot be fully reduced to deterministic string checks. GenLayer supplies the independent leader/validator execution and shared accepted outcome. Deterministic code controls identities, state transitions, schema, quotation provenance and aggregate results. A conventional local LLM answer alone cannot create this shared on-chain record.

## References

- [GenLayer equivalence principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [Testing intelligent contracts](https://docs.genlayer.com/developers/intelligent-contracts/testing)
- [Direct-mode testing API](https://docs.genlayer.com/api-references/genlayer-test/direct)
- [GenVM v0.3.0-rc7 release](https://github.com/genlayerlabs/genvm/releases/tag/v0.3.0-rc7)

Portal acceptance, BP awards, conversion into GLP, airdrop eligibility and token value are not established by this package.
