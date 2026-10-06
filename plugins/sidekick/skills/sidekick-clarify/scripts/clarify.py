#!/usr/bin/env python3
"""clarify.py render|merge <state_dir> [answers.json] [--open]"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "questions.html")


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def render(state, open_it):
    data = load(os.path.join(state, "questions.json"), {"channel": os.path.basename(state), "questions": []})
    payload = json.dumps(data).replace("</", "<\\/")
    with open(TEMPLATE) as f:
        html = f.read().replace("__QUESTIONS_PLACEHOLDER__", payload)
    out = os.path.join(state, "clarify.html")
    with open(out, "w") as f:
        f.write(html)
    n = sum(1 for q in data["questions"] if q.get("status") == "open")
    print(f"{out} ({n} open)")
    if open_it and n:
        subprocess.run(["open", out], check=False)


def newest_download():
    files = glob.glob(os.path.expanduser("~/Downloads/answers*.json"))
    return max(files, key=os.path.getmtime) if files else None


def merge(state, answers_path):
    answers_path = answers_path or newest_download()
    if not answers_path:
        sys.exit("no answers file found; pass a path or export from the page first")
    new = load(answers_path, {})
    qpath = os.path.join(state, "questions.json")
    data = load(qpath, {"questions": []})
    byid = {q["id"]: q for q in data["questions"]}
    stored = load(os.path.join(state, "answers.json"), {})
    lines = []
    for qid, a in new.items():
        q = byid.get(qid)
        if not q or q.get("status") == "answered":
            continue
        stored[qid] = a
        q["status"] = "answered"
        parts = [p for p in (a.get("choice"), a.get("text")) if p]
        lines.append(f"- [{q.get('category', 'general')}] {q['question']} -> {'; '.join(parts)}")
    with open(os.path.join(state, "answers.json"), "w") as f:
        json.dump(stored, f, indent=2)
    with open(qpath, "w") as f:
        json.dump(data, f, indent=2)
    if lines:
        ppath = os.path.join(state, "profile.md")
        text = open(ppath).read() if os.path.exists(ppath) else "# profile\n"
        if "## Operator guidance" not in text:
            text = text.rstrip("\n") + "\n\n## Operator guidance\n"
        text = text.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
        with open(ppath, "w") as f:
            f.write(text)
    print(f"merged {len(lines)} answers from {answers_path}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--open"]
    if len(args) < 2 or args[0] not in ("render", "merge"):
        sys.exit(__doc__)
    state = os.path.expanduser(args[1])
    if args[0] == "render":
        render(state, "--open" in sys.argv)
    else:
        merge(state, args[2] if len(args) > 2 else None)
