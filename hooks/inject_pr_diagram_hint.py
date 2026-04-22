#!/usr/bin/env python3
"""UserPromptSubmit hook for the pr-sequence-diagram plugin.

Detects prompts that ask for PR/branch/diff comprehension and injects
context instructing Claude to invoke the pr-sequence-diagram skill inline
in its response. Stays silent otherwise.
"""
import json
import re
import sys

ADDITIONAL_CONTEXT = (
    "This prompt looks like a PR/branch/diff comprehension request. "
    "Lead your response with a one-sentence motive caption and a Mermaid "
    "sequence diagram (at most 6 participants, at most 10 arrows) via the "
    "pr-sequence-diagram skill — emit it inline in the chat, before any "
    "line-by-line review notes. Do not save a sidecar file unless the user "
    "explicitly asks for a pinnable copy. Skip the diagram entirely if the "
    "diff is trivial (pure docs, tests, formatting, typo fix) or the user "
    "opted out."
)

SLASH_RE = re.compile(r'(?:^|[^a-z0-9/])/(?:review|security-review)(?:\b|[^a-z0-9]|$)')
VERB_RE = re.compile(
    r'(review|summari[sz]e|explain|walk[ -]?(?:me|through)|tl[^a-z]?;?dr'
    r'|diagram|visuali[sz]e|motive|what[^a-z]{0,20}does)'
)
NOUN_RE = re.compile(r'\b(pr|branch|diff|changes|commits|merge request|pull request)\b')
OPT_OUT_RE = re.compile(
    r'\b(skip|no|without)[^a-z]{0,10}(?:the )?(?:diagram|sequence diagram|visual)\b'
)


def should_trigger(prompt: str) -> bool:
    lower = prompt.lower()
    if SLASH_RE.search(lower):
        triggered = True
    elif VERB_RE.search(lower) and NOUN_RE.search(lower):
        triggered = True
    else:
        triggered = False
    if OPT_OUT_RE.search(lower):
        triggered = False
    return triggered


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    prompt = data.get("prompt") or ""
    if not prompt:
        return
    if should_trigger(prompt):
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ADDITIONAL_CONTEXT,
            }
        }, sys.stdout)


if __name__ == "__main__":
    main()
