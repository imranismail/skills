# Imran's Skills

A personal collection of [Claude Code](https://docs.claude.com/claude-code) skills, distributed as a plugin marketplace.

## Skills

### pr-sequence-diagram

Renders a high-level Mermaid sequence diagram of a PR's diff vs. its base branch — a one-glance visual summary a reviewer can digest in 5-15 seconds.

**Triggers on:** diagramming a PR/branch, visualizing a diff, asking "what does this PR do" post-`/review`.

**Output:** a markdown file at `.claude/pr-diagrams/<branch>.md` inside the repo, opened in VS Code.

## Installation

Inside a Claude Code session:

```
/plugin marketplace add imranismail/skills
/plugin install pr-sequence-diagram@imrans-skills
/reload-plugins
```

Replace the marketplace source with a local path (e.g. `/plugin marketplace add /Users/you/Projects/skills`) when developing locally.

## Triggering

The skill itself is model-invoked — Claude can discover it automatically — but bare `/review` and other short branch-comprehension prompts don't reliably consult specialty skills. To close that gap, the plugin ships a `UserPromptSubmit` hook (`hooks/inject_pr_diagram_hint.py`) that detects prompts like `/review`, "summarise this PR", "walk me through this branch", etc. and injects an instruction for Claude to invoke the skill. Prompts that aren't branch-scoped (reviewing a pasted function, summarizing a Slack thread, asking for a generic OAuth diagram) stay silent.

Opt out for a given prompt by saying "skip the diagram".

## Layout

```
.claude-plugin/
  marketplace.json     # marketplace metadata
  plugin.json          # plugin metadata
skills/
  pr-sequence-diagram/
    SKILL.md           # skill definition
    evals/             # test fixtures + trigger evals
```

## Development

The `*-workspace/` directories contain eval runs and are gitignored — they're only used while iterating on skills with the skill-creator workflow.
