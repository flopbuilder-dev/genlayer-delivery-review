# Validation report — 21 October 2026

This is an author-prepared validation record, not an independent security audit or a GenLayer acceptance decision. Development was assisted by AI.

## Results

| Check | Result | Practical limit |
| --- | --- | --- |
| GenVM static safety lint | Passed; no lint warnings in the final check | Static analysis cannot establish model reliability |
| GenVM SDK semantic validation | Passed: 1 contract, 3 writes, 1 view, 2 constructor parameters | An informational notice says a newer runner exists; this contract pins the runner used by the official boilerplate inspected during development |
| SDK direct-mode tests | **55 passed**, 0 failures, 5.29 seconds | All model responses are supplied fixtures; these are not 55 live AI tests |
| Studio deployment | FINALIZED; GenVM SUCCESS; consensus Accepted | Studionet sandbox, not Bradbury or mainnet |
| Assigned-worker submission | FINALIZED; GenVM SUCCESS; consensus Accepted | One synthetic text example |
| Live semantic assessment | FINALIZED; GenVM SUCCESS; consensus Accepted | A majority disagreement caused a leader rotation before acceptance |
| Finalized state read | `assessment_recorded`; both criteria `met`; overall `met` | Tests presence of two commands in text, not whether those commands work |
| Portal submission / points | Not submitted / not established | Acceptance, BP, GLP and eligibility are separate decisions |

The formal direct-test record is `pytest.xml`. Exact tool versions, SDK digest and contract digest are in `environment.json`. The direct-test framework's default localnet configuration messages do not mean those tests contacted a network; direct mode executes in-process.

## Live evidence

Contract: `0xD5C585E0f82ad85E7BCcb4401ABB4Ede807dc67b`

[Public contract and source](https://explorer-studio.genlayer.com/address/0xD5C585E0f82ad85E7BCcb4401ABB4Ede807dc67b)

| Operation | Transaction |
| --- | --- |
| Deploy | `0x6c5a5293d634857b67ca4f403f9059d0de1526d729bf48804142bf319cd08af2` |
| submit_delivery | `0xe0bf110c308fe36051365763d25cd938df04df114628a38e430f03dd5d0efc47` |
| assess_delivery | `0x8dd872819ea549cb8203f20d43de67b2c6058ceed73f16014af1a856a32b5116` |

Studio was set to **Normal (Full Consensus)**. Simulation Mode was unchecked. Separate new sandbox accounts represented requester and worker. Neither was the user's Portal wallet. No user funds, API credentials or mainnet ETH were used. A read was explicitly requested against **Finalized** state after the assessment finalized; success was not inferred merely from an Accepted transaction.

The finalized result contained:

```json
{"decisions":[{"id":"install","status":"met","basis":"supported","quote":"pip install demo"},{"id":"execute","status":"met","basis":"supported","quote":"python demo.py"}],"overall":"met"}
```

The delivered text was `Install: pip install demo. Run: python demo.py.` This is an intentionally simple synthetic example. It establishes one working full execution path, including closure serialization and actual inference, but not broad correctness, resistance to prompt injection, fair judgment, reliable liveness or a latency/fee guarantee. An initial leader disagreement/rotation was visible and should inform further evaluation.

The Studio editor was named `storage.py`; its contents were replaced with `DeliveryReview` before deployment. The deployed source and ABI identify the new contract. During editing, an automatic schema request logged `invalid_contract absent_runner_comment` while the editor was transiently empty. That is not the outcome of the deployed contract: the explorer independently shows SUCCESS for all three final transactions and exposes the correct source.

## Direct test coverage

The tests exercise ownership and role checks, disallowed self/zero worker assignment, malformed and duplicate requirements, UTF-8 byte limits, immutable submissions, pre-submission cancellation, cancellation closure after submission, assessment access, prevention of repeated assessments, deterministic aggregation across every pair of the three statuses, grounding of quotations, independent validator agreement/disagreement, rejection of fabricated leader evidence, malformed model results and failed validator inference. The external-fact example checks the application path using a mocked insufficient-evidence response; it does not measure whether a real model always makes that distinction.

## Remaining work

1. Review the Portal's separate full-guidelines page, including any ownership, attribution and AI-assistance policies, before submission. The category rubric in the supplied recording was reviewed.
2. Verify the source/test/documentation publication at https://github.com/flopbuilder-dev/genlayer-delivery-review and attach it as further evidence in the Portal submission. The public explorer also exposes the deployed source.
3. Broaden live examples and adversarial evaluation before any production use. No audit, funded escrow or financial deployment is implied.

Review timing on the Portal is stated as 1–2 weeks. This work does not establish that Season 1 deadlines can be met.
