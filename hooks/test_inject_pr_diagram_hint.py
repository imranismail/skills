"""Tests for the pr-sequence-diagram UserPromptSubmit hook's trigger logic.

The hook is pure: prompt string in, bool out. No mocking needed.

Run: python3 -m unittest hooks/test_inject_pr_diagram_hint.py
Or:  python3 hooks/test_inject_pr_diagram_hint.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inject_pr_diagram_hint import should_trigger  # noqa: E402


POSITIVE_CASES = [
    "/review",
    "/security-review",
    "/review 123",
    "/review https://github.com/acme/repo/pull/42",
    "please /review this branch",
    "walk me through this branch",
    "walk-through this PR",
    "summarise this PR",
    "summarize these changes",
    "what does this PR do",
    "what does this diff change",
    "diagram this PR",
    "diagram this merge request",
    "visualize the branch",
    "tl;dr this PR",
    "tldr the diff",
    "explain these changes",
    "review the PR",
    "review this pull request",
    "review this merge request",
    "help me understand this PR",
    "help me understand these changes",
    "understand this diff",
    "grok these changes",
]

NEGATIVE_CASES = [
    "review this paragraph for tone",
    "explain how rebases work",
    "summarize this article for me",
    "walk me through installing Python",
    "what does this function do",
    "diagram a database schema",
    "/help",
    "visualize the sorting algorithm",
    "explain the concept of currying",
    "help me understand how promises work",
    "I understand the tradeoffs already",
    "understand what you mean",
]

OPT_OUT_CASES = [
    "/review but skip the diagram",
    "/security-review, text only",
    "/review, text-only",
    "review this PR, no mermaid",
    "walk me through this branch, don't diagram it",
    "summarise this PR without the diagram",
    "review the diff, just the notes",
    "/review — skip the visual",
    "/review no sequence diagram please",
    "/review just the review",
]


class TriggerLogicTests(unittest.TestCase):
    def test_positive_triggers(self):
        for prompt in POSITIVE_CASES:
            with self.subTest(prompt=prompt):
                self.assertTrue(should_trigger(prompt), f"expected trigger for: {prompt!r}")

    def test_negative_does_not_trigger(self):
        for prompt in NEGATIVE_CASES:
            with self.subTest(prompt=prompt):
                self.assertFalse(should_trigger(prompt), f"expected no trigger for: {prompt!r}")

    def test_opt_out_suppresses(self):
        for prompt in OPT_OUT_CASES:
            with self.subTest(prompt=prompt):
                self.assertFalse(should_trigger(prompt), f"expected opt-out for: {prompt!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
