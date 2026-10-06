# Imran's Skills

A personal collection of [Claude Code](https://docs.claude.com/claude-code) skills, distributed as a plugin marketplace.

## Skills

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
/plugin install sidekick@imrans-skills
/reload-plugins
```

Replace the marketplace source with a local path (e.g. `/plugin marketplace add /Users/you/Projects/skills`) when developing locally.

## Retired

`pr-sequence-diagram` has been sunset. It is removed from the catalog and listed under `renames` in `marketplace.json` with a `null` target, which is how Claude Code marks a plugin as removed.

## Layout

```
.claude-plugin/
  marketplace.json     # marketplace catalog
plugins/
  sidekick/
    .claude-plugin/plugin.json
    skills/            # sidekick, sidekick-setup, -refresh, -oncall, -clarify
```

## Development

The `*-workspace/` directories contain eval runs and are gitignored. They are only used while iterating on skills with the skill-creator workflow.
