"""Grade a pr-sequence-diagram eval response against assertion criteria.

Usage:
    python grader.py --response <path> --fixture <name> --prompt-class <class> \
                     --output <grading.json>

Fixtures:
    node-api-stripe-cancel, python-queue-welcome-emails, react-onboarding-flag
        -> expect diagram
    pure-refactor, trivial-docs
        -> expect NO diagram

Prompt classes:
    review          -> /review; expect diagram prepended
    security-review -> /security-review; expect diagram prepended
    diagram-only    -> "diagram this PR"; expect diagram alone
    walkthrough     -> "walk me through this branch"; expect diagram
    opt-out         -> "/review, text only"; expect NO diagram
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


NO_DIAGRAM_FIXTURES = {"pure-refactor", "trivial-docs"}
REVIEW_PROMPT_CLASSES = {"review", "security-review"}


MERMAID_FENCE_RE = re.compile(
    r"```mermaid\s*\n(sequenceDiagram[\s\S]*?)```",
    re.MULTILINE,
)
PARTICIPANT_RE = re.compile(r"^\s*(?:participant|actor)\s+\w", re.MULTILINE)
ARROW_RE = re.compile(r"^\s*\w[\w -]*\s*(?:->>|-->>|->>\+|-->>-)\s*\w", re.MULTILINE)
ACTIVATION_RE = re.compile(r"(?:->>\+|-->>-)")
BLOCK_RE = re.compile(r"^\s*(?:alt|opt|loop|par)\b", re.MULTILINE)
FILE_EXT_RE = re.compile(r"\.(?:py|ts|tsx|js|jsx|rb|go|rs|java|kt|cs|cpp|c|h|hpp|php)\b")
METHOD_CALL_RE = re.compile(r"\b[a-zA-Z_]\w*\(\s*[^)]*\)")


@dataclass
class Expectation:
    text: str
    passed: bool
    evidence: str = ""


@dataclass
class Grade:
    eval_id: str
    expectations: list[Expectation] = field(default_factory=list)

    def add(self, text: str, passed: bool, evidence: str = "") -> None:
        self.expectations.append(Expectation(text=text, passed=passed, evidence=evidence))

    def to_dict(self) -> dict:
        return {
            "eval_id": self.eval_id,
            "expectations": [
                {"text": e.text, "passed": e.passed, "evidence": e.evidence}
                for e in self.expectations
            ],
            "passed": all(e.passed for e in self.expectations),
        }


def extract_fence(response: str) -> tuple[str | None, int | None]:
    """Return (fence body, line index of fence start) or (None, None)."""
    match = MERMAID_FENCE_RE.search(response)
    if not match:
        return None, None
    line_index = response[: match.start()].count("\n")
    return match.group(1), line_index


def extract_caption(response: str, fence_start_line: int) -> str:
    """The caption is the last non-empty line above the fence, ignoring headings."""
    lines = response.split("\n")
    for i in range(fence_start_line - 1, -1, -1):
        line = lines[i].strip()
        if not line:
            continue
        # Skip markdown headings
        if line.startswith("#"):
            continue
        return line
    return ""


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def grade_expect_diagram(response: str, prompt_class: str, grade: Grade) -> None:
    fence, fence_line = extract_fence(response)
    grade.add(
        "response contains a Mermaid sequenceDiagram fence",
        fence is not None,
        evidence=("fence found" if fence else "no ```mermaid\\nsequenceDiagram``` block"),
    )
    if fence is None:
        return

    participants = PARTICIPANT_RE.findall(fence)
    participant_count = len(participants)
    grade.add(
        "participant count ≤ 6",
        participant_count <= 6,
        evidence=f"{participant_count} participant(s)",
    )

    arrows = ARROW_RE.findall(fence)
    arrow_count = len(arrows)
    grade.add(
        "arrow count ≤ 10",
        arrow_count <= 10,
        evidence=f"{arrow_count} arrow(s)",
    )

    activation_hits = ACTIVATION_RE.findall(fence)
    grade.add(
        "no activation bars (->>+ / -->>-) unless lifetime matters",
        len(activation_hits) == 0,
        evidence=f"{len(activation_hits)} activation-bar usage(s)",
    )

    blocks = BLOCK_RE.findall(fence)
    grade.add(
        "at most one alt/opt/loop/par block",
        len(blocks) <= 1,
        evidence=f"{len(blocks)} block(s): {blocks}",
    )

    label_lines = [ln for ln in fence.split("\n") if ("->>" in ln or "-->>" in ln)]
    file_ext_hits = [ln for ln in label_lines if FILE_EXT_RE.search(ln)]
    grade.add(
        "no file extensions in arrow labels",
        len(file_ext_hits) == 0,
        evidence=(f"offending label(s): {file_ext_hits}" if file_ext_hits else ""),
    )

    method_call_hits = [ln for ln in label_lines if METHOD_CALL_RE.search(ln)]
    grade.add(
        "no method-call syntax in arrow labels",
        len(method_call_hits) == 0,
        evidence=(f"offending label(s): {method_call_hits}" if method_call_hits else ""),
    )

    caption = extract_caption(response, fence_line or 0)
    wc = word_count(caption)
    grade.add(
        "caption ≤ 25 words",
        wc <= 25,
        evidence=f"{wc} words: {caption!r}",
    )
    terminals = sum(caption.count(c) for c in ".!?")
    grade.add(
        "caption is a single sentence (one terminal .!?)",
        terminals == 1,
        evidence=f"{terminals} terminal punctuation mark(s)",
    )

    if prompt_class in REVIEW_PROMPT_CLASSES:
        total_lines = response.count("\n") + 1
        fence_ratio = (fence_line or 0) / max(1, total_lines)
        grade.add(
            "diagram appears in the first half of the review response",
            fence_ratio <= 0.5,
            evidence=f"fence starts at line {fence_line} of {total_lines} ({fence_ratio:.0%})",
        )


def grade_expect_no_diagram(response: str, grade: Grade) -> None:
    fence, _ = extract_fence(response)
    grade.add(
        "response contains NO Mermaid sequenceDiagram fence",
        fence is None,
        evidence=("no fence found" if fence is None else "fence unexpectedly present"),
    )


def run_grading(response: str, fixture: str, prompt_class: str, eval_id: str) -> Grade:
    grade = Grade(eval_id=eval_id)
    expect_diagram = fixture not in NO_DIAGRAM_FIXTURES and prompt_class != "opt-out"
    if expect_diagram:
        grade_expect_diagram(response, prompt_class, grade)
    else:
        grade_expect_no_diagram(response, grade)
    return grade


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", required=True, type=Path)
    parser.add_argument("--fixture", required=True)
    parser.add_argument(
        "--prompt-class",
        required=True,
        choices=["review", "security-review", "diagram-only", "walkthrough", "opt-out"],
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--eval-id", default="")
    args = parser.parse_args()

    if not args.response.exists():
        print(f"response file not found: {args.response}", file=sys.stderr)
        return 1

    response = args.response.read_text()
    eval_id = args.eval_id or f"{args.fixture}-{args.prompt_class}"
    grade = run_grading(response, args.fixture, args.prompt_class, eval_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(grade.to_dict(), indent=2))
    passed = grade.to_dict()["passed"]
    print(f"{eval_id}: {'PASS' if passed else 'FAIL'} ({args.output})")
    for exp in grade.expectations:
        mark = "✓" if exp.passed else "✗"
        line = f"  {mark} {exp.text}"
        if exp.evidence:
            line += f" — {exp.evidence}"
        print(line)
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
