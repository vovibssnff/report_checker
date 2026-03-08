from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.checkers.base import BaseRule
from app.checkers.registry import RuleRegistry
from app.core.domain.value_objects import DocumentType, Severity


def _make_rule(
    code: str,
    doc_type: DocumentType = DocumentType.VKR_TEMPLATE,
    severity: Severity = Severity.ERROR,
) -> BaseRule:
    r = MagicMock(spec=BaseRule)
    r.code = code
    r.name = f"Rule {code}"
    r.description = ""
    r.document_type = doc_type
    r.default_severity = severity
    r.default_config = {}
    return r


@pytest.fixture()
def registry():
    return RuleRegistry()


class TestRegister:
    def test_register_and_retrieve(self, registry):
        rule = _make_rule("test.rule.1")
        registry.register(rule)

        all_rules = registry.all_rules()
        assert len(all_rules) == 1
        assert all_rules[0].code == "test.rule.1"

    def test_duplicate_raises(self, registry):
        rule1 = _make_rule("dup.code")
        rule2 = _make_rule("dup.code")

        registry.register(rule1)
        with pytest.raises(ValueError, match="Duplicate rule code"):
            registry.register(rule2)


class TestGetRules:
    def test_filters_by_document_type(self, registry):
        vkr_rule = _make_rule("vkr.r1", doc_type=DocumentType.VKR_TEMPLATE)
        practice_rule = _make_rule("practice.r1", doc_type=DocumentType.PRACTICE_REPORT)
        registry.register(vkr_rule)
        registry.register(practice_rule)

        vkr_rules = registry.get_rules(DocumentType.VKR_TEMPLATE)
        assert len(vkr_rules) == 1
        assert vkr_rules[0].code == "vkr.r1"

        practice_rules = registry.get_rules(DocumentType.PRACTICE_REPORT)
        assert len(practice_rules) == 1
        assert practice_rules[0].code == "practice.r1"

    def test_filters_by_enabled_codes(self, registry):
        r1 = _make_rule("a.1")
        r2 = _make_rule("a.2")
        r3 = _make_rule("a.3")
        registry.register(r1)
        registry.register(r2)
        registry.register(r3)

        result = registry.get_rules(DocumentType.VKR_TEMPLATE, enabled_codes={"a.1", "a.3"})
        codes = {r.code for r in result}
        assert codes == {"a.1", "a.3"}

    def test_enabled_codes_none_returns_all_for_type(self, registry):
        r1 = _make_rule("b.1")
        r2 = _make_rule("b.2")
        registry.register(r1)
        registry.register(r2)

        result = registry.get_rules(DocumentType.VKR_TEMPLATE, enabled_codes=None)
        assert len(result) == 2

    def test_empty_registry(self, registry):
        result = registry.get_rules(DocumentType.VKR_TEMPLATE)
        assert result == []


class TestAllRules:
    def test_returns_all_registered(self, registry):
        r1 = _make_rule("x.1", doc_type=DocumentType.VKR_TEMPLATE)
        r2 = _make_rule("x.2", doc_type=DocumentType.PRACTICE_REPORT)
        registry.register(r1)
        registry.register(r2)

        assert len(registry.all_rules()) == 2
