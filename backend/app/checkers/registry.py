from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from app.checkers.base import BaseRule
    from app.core.domain.value_objects import DocumentType


class RuleRegistry:
    _instance: ClassVar[RuleRegistry | None] = None

    def __init__(self) -> None:
        self._rules: dict[str, BaseRule] = {}

    @classmethod
    def instance(cls) -> RuleRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, rule: BaseRule) -> None:
        if rule.code in self._rules:
            raise ValueError(f"Duplicate rule code: {rule.code}")
        self._rules[rule.code] = rule

    def get_rules(
        self,
        doc_type: DocumentType,
        enabled_codes: set[str] | None = None,
    ) -> list[BaseRule]:
        matched = [r for r in self._rules.values() if r.document_type == doc_type]
        if enabled_codes is not None:
            matched = [r for r in matched if r.code in enabled_codes]
        return matched

    def all_rules(self) -> list[BaseRule]:
        return list(self._rules.values())

    def discover_plugins(self) -> None:
        import app.checkers.plugins as plugins_pkg

        for _importer, modname, _ispkg in pkgutil.walk_packages(
            plugins_pkg.__path__,
            prefix=plugins_pkg.__name__ + ".",
        ):
            importlib.import_module(modname)  # nosemgrep
