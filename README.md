# Imran's Skills

A personal collection of [Claude Code](https://docs.claude.com/claude-code) skills, distributed as a plugin marketplace.

## Skills

### pr-sequence-diagram

Renders a high-level Mermaid sequence diagram of a PR's diff vs. its base branch — a one-glance visual summary a reviewer can digest in 5-15 seconds.

**Triggers on:** diagramming a PR/branch, visualizing a diff, asking "what does this PR do" post-`/review`.

**Output:** a markdown file at `.claude/pr-diagrams/<branch>.md` inside the repo, opened in VS Code.

### sidekick

A sidekick for any Slack support channel. Nothing channel-specific is built in: it learns the channel, then serves requests from what it learned.

| Skill | Purpose |
|---|---|
| `sidekick-setup` | Scan a channel's history and threads, build its profile, seed episodes, queue questions |
| `sidekick-refresh` | Update the profile from messages since the last run |
| `sidekick-oncall` | Self-paced loop over new requests: recall, draft a reply, never post |
| `sidekick-clarify` | Local HTML page to answer the sidekick's open questions |
| `sidekick` | Handle one request (classify, recall, serve, store), plus `status`, `forget`, `remember` |

Memory is plain markdown files under `~/.claude/sidekick/<channel>/` (override with `SIDEKICK_HOME`). Recall is text search over episodes. Everything stays on your machine, and replies are drafts only.

## Installation

Inside a Claude Code session:

```
/plugin marketplace add imranismail/skills
/plugin install pr-sequence-diagram@imrans-skills
/plugin install sidekick@imrans-skills
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
plugins/
  sidekick/
    .claude-plugin/plugin.json
    skills/            # sidekick, sidekick-setup, -refresh, -oncall, -clarify
```

## Development

The `*-workspace/` directories contain eval runs and are gitignored — they're only used while iterating on skills with the skill-creator workflow.
