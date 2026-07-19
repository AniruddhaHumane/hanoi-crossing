"""Smoke test: proves the package imports and the test pipeline runs.

Committed alongside the pre-commit / CI setup, before any engine code exists —
the first step of a test-first workflow.
"""

import hanoi


def test_package_imports():
    assert hanoi.__version__
