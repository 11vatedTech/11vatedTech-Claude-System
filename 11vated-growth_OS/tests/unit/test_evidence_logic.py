"""Evidence truth-class invariants."""

import pytest

from growthos.domain.enums import TruthClass
from growthos.intelligence.evidence import _assert_raw_truth_class, _content_hash
from growthos.shared.errors import ValidationError


def test_raw_evidence_must_be_fact_or_observation():
    _assert_raw_truth_class(TruthClass.FACT)
    _assert_raw_truth_class(TruthClass.OBSERVATION)


def test_inference_rejected_as_raw_evidence():
    with pytest.raises(ValidationError):
        _assert_raw_truth_class(TruthClass.INFERENCE)
    with pytest.raises(ValidationError):
        _assert_raw_truth_class(TruthClass.HYPOTHESIS)


def test_content_hash_is_deterministic():
    assert _content_hash("same text") == _content_hash("same text")
    assert _content_hash("same text") != _content_hash("different")
