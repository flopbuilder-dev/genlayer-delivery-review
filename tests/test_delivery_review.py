"""SDK direct-mode tests. Model outputs are fixtures, not live AI assessments."""

import json
import pytest

CONTRACT = "contracts/delivery_review.py"
REQUIREMENTS = [
    {"id": "install", "requirement": "Include a concrete installation command in the delivered text."},
    {"id": "execute", "requirement": "Include a concrete command for running the program."},
]
DELIVERY = "Install: pip install demo. Run: python demo.py."


def addr_hex(value):
    return ("0x" + value.hex()) if isinstance(value, bytes) else value.as_hex.lower()


def decision(ident, status="met", basis="supported", quote="pip install demo"):
    return {"id": ident, "status": status, "basis": basis, "quote": quote}


def answer(first=None, second=None):
    return {"decisions": [
        first or decision("install"),
        second or decision("execute", quote="python demo.py"),
    ]}


@pytest.fixture
def review(direct_deploy, direct_alice):
    return direct_deploy(CONTRACT, addr_hex(direct_alice), json.dumps(REQUIREMENTS))


def submit(review, direct_vm, direct_alice, text=DELIVERY):
    direct_vm.sender = direct_alice
    review.submit_delivery(text)


def assess(review, direct_vm, response):
    direct_vm.mock_llm(r"[\s\S]*", json.dumps(response))
    review.assess_delivery()


def test_frozen_initial_record(review, direct_owner, direct_alice):
    record = review.get_record()
    record["requester"] = record["requester"].lower()
    record["worker"] = record["worker"].lower()
    assert record == {
        "requester": addr_hex(direct_owner),
        "worker": addr_hex(direct_alice),
        "requirements": REQUIREMENTS,
        "delivery": "", "stage": "open", "assessment": None,
    }


@pytest.mark.parametrize("requirements", [
    [], [{"id": "x", "requirement": "a"}] * 9,
    [{"id": "x", "requirement": "a"}, {"id": "x", "requirement": "b"}],
    [{"id": "INVALID!", "requirement": "a"}],
    [{"id": "x", "requirement": ""}],
    [{"id": "x", "requirement": " "}],
    [{"id": "x", "requirement": "a" * 601}],
    [{"id": "x", "requirement": "a", "extra": True}],
    {"id": "x", "requirement": "a"},
])
def test_invalid_specs_rejected(direct_deploy, direct_alice, requirements):
    with pytest.raises(Exception):
        direct_deploy(CONTRACT, addr_hex(direct_alice), json.dumps(requirements))


def test_oversized_spec_rejected(direct_deploy, direct_alice):
    with pytest.raises(Exception, match="too large"):
        direct_deploy(CONTRACT, addr_hex(direct_alice), " " * 8193)


@pytest.mark.parametrize("worker", ["0x" + "0" * 40, "bad-address"])
def test_invalid_worker_rejected(direct_deploy, worker):
    with pytest.raises(Exception):
        direct_deploy(CONTRACT, worker, json.dumps(REQUIREMENTS))


def test_self_assignment_rejected(direct_deploy, direct_owner):
    with pytest.raises(Exception, match="separate"):
        direct_deploy(CONTRACT, addr_hex(direct_owner), json.dumps(REQUIREMENTS))


def test_requester_cannot_impersonate_worker(review):
    with pytest.raises(Exception, match="Only assigned worker"):
        review.submit_delivery(DELIVERY)
    assert review.get_record()["stage"] == "open"


def test_outsider_cannot_submit_or_assess(review, direct_vm, direct_bob):
    direct_vm.sender = direct_bob
    with pytest.raises(Exception, match="Only assigned worker"):
        review.submit_delivery(DELIVERY)
    with pytest.raises(Exception, match="Only requester or worker"):
        review.assess_delivery()


@pytest.mark.parametrize("delivery", ["", " \n\t", "x" * 24577, "é" * 12289])
def test_delivery_limits(review, direct_vm, direct_alice, delivery):
    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="UTF-8 bytes"):
        review.submit_delivery(delivery)
    assert review.get_record()["stage"] == "open"


def test_submission_freezes_delivery(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    with pytest.raises(Exception, match="closed"):
        review.submit_delivery("revised text")
    assert review.get_record()["delivery"] == DELIVERY


def test_cancellation_before_submission(review):
    review.cancel_before_submission()
    assert review.get_record()["stage"] == "cancelled"


def test_cancelled_record_cannot_be_submitted(review, direct_vm, direct_alice):
    review.cancel_before_submission()
    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="closed"):
        review.submit_delivery(DELIVERY)


def test_worker_cannot_cancel(review, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="Only requester"):
        review.cancel_before_submission()


def test_requester_cannot_cancel_after_delivery(review, direct_vm, direct_alice, direct_owner):
    submit(review, direct_vm, direct_alice)
    direct_vm.sender = direct_owner
    with pytest.raises(Exception, match="closed"):
        review.cancel_before_submission()


def test_no_assessment_before_delivery(review):
    with pytest.raises(Exception, match="submitted deliverable"):
        review.assess_delivery()


def test_supported_result_and_validator_agreement(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    result = review.get_record()
    assert result["stage"] == "assessment_recorded"
    assert result["assessment"]["overall"] == "met"
    assert direct_vm.run_validator() is True


def test_requester_can_assess(review, direct_vm, direct_alice, direct_owner):
    submit(review, direct_vm, direct_alice)
    direct_vm.sender = direct_owner
    assess(review, direct_vm, answer())
    assert review.get_record()["assessment"]["overall"] == "met"


def test_no_result_shopping(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    with pytest.raises(Exception, match="submitted deliverable"):
        review.assess_delivery()


def test_independent_validator_can_disagree(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    direct_vm.clear_mocks()
    direct_vm.mock_llm(r"[\s\S]*", json.dumps(answer(second=decision("execute", "unmet", "missing", ""))))
    assert direct_vm.run_validator() is False


def test_same_decision_different_grounded_quotes_agree(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    direct_vm.clear_mocks()
    direct_vm.mock_llm(r"[\s\S]*", json.dumps(answer(first=decision("install", quote="Install: pip install demo."))))
    assert direct_vm.run_validator() is True


def test_validator_rejects_fabricated_leader_quote(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    assert direct_vm.run_validator(leader_result=answer(first=decision("install", quote="fabricated evidence"))) is False


def test_validator_rejects_leader_error(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    assert direct_vm.run_validator(leader_error=ValueError("inference failed")) is False


def test_validator_failure_cannot_approve(review, direct_vm, direct_alice):
    submit(review, direct_vm, direct_alice)
    assess(review, direct_vm, answer())
    direct_vm.clear_mocks()
    direct_vm.mock_llm(r"[\s\S]*", "not-json")
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize("response", [
    {"decisions": []}, {"decisions": [decision("install")]},
    {"decisions": [decision("install"), decision("install")]},
    {"decisions": [decision("execute"), decision("install")]},
    answer(first=decision("install", quote="not in delivery")),
    answer(first=decision("install", quote="")),
    answer(first=decision("install", "met", "missing", "")),
    answer(first=decision("install", "insufficient_evidence", "unverifiable", "pip install demo")),
    {"decisions": [{"id": "install", "status": "met", "basis": "supported", "quote": "pip install demo", "extra": "x"}, decision("execute")]},
    {"decisions": [decision("install"), decision("execute")], "overall": "met"},
])
def test_malformed_model_output_preserves_submitted_state(review, direct_vm, direct_alice, response):
    submit(review, direct_vm, direct_alice)
    with pytest.raises(Exception):
        assess(review, direct_vm, response)
    record = review.get_record()
    assert record["stage"] == "submitted"
    assert record["assessment"] is None


@pytest.mark.parametrize("statuses,overall", [
    (("met", "met"), "met"),
    (("met", "insufficient_evidence"), "insufficient_evidence"),
    (("insufficient_evidence", "met"), "insufficient_evidence"),
    (("insufficient_evidence", "insufficient_evidence"), "insufficient_evidence"),
    (("unmet", "met"), "unmet"), (("met", "unmet"), "unmet"),
    (("unmet", "unmet"), "unmet"),
    (("unmet", "insufficient_evidence"), "unmet"),
    (("insufficient_evidence", "unmet"), "unmet"),
])
def test_aggregate_is_derived_deterministically(review, direct_vm, direct_alice, statuses, overall):
    submit(review, direct_vm, direct_alice)
    entries = []
    for i, status in enumerate(statuses):
        basis, quote = {
            "met": ("supported", ["pip install demo", "python demo.py"][i]),
            "unmet": ("missing", ""),
            "insufficient_evidence": ("unverifiable", ""),
        }[status]
        entries.append(decision(REQUIREMENTS[i]["id"], status, basis, quote))
    assess(review, direct_vm, {"decisions": entries})
    assert review.get_record()["assessment"]["overall"] == overall


def test_explicit_contradiction_is_grounded(review, direct_vm, direct_alice):
    text = "Install: pip install demo. This program cannot be run yet."
    submit(review, direct_vm, direct_alice, text)
    assess(review, direct_vm, answer(second=decision("execute", "unmet", "contradicted", "cannot be run yet")))
    assert review.get_record()["assessment"]["overall"] == "unmet"


def test_external_fact_remains_unverified(direct_deploy, direct_vm, direct_alice):
    criteria = [{"id": "runtime", "requirement": "The software's test suite actually passes when executed."}]
    contract = direct_deploy(CONTRACT, addr_hex(direct_alice), json.dumps(criteria))
    submit(contract, direct_vm, direct_alice, "I claim all tests passed.")
    assess(contract, direct_vm, {"decisions": [decision("runtime", "insufficient_evidence", "unverifiable", "")]})
    assert contract.get_record()["assessment"]["overall"] == "insufficient_evidence"
