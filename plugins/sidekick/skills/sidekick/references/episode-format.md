# Episode format

One file per resolved request: `<state root>/<channel-slug>/episodes/<yyyy-mm>-<category>-<short-slug>.md`

```markdown
---
channel: <channel-slug>
category: <category-slug from profile.md>
symptom: <one line in the requester's words, plus the key error string>
tags: [<resource>, <tool>, <error-fragment>]
first_seen: 2026-09-10
last_seen: 2026-09-10
occurrences: 1
outcome: resolved | partial | unconfirmed
source: observed | user-stated | backfilled
---

## Context
One or two lines: system, environment, what was being attempted.

## Root cause
What actually caused it, or "unknown" if never found.

## Resolution
Numbered steps that fixed it, with exact commands or settings (no secret values).

## Why / how to apply
When this episode applies, what to re-verify first, and what would make it stale.

## Occurrences
- 2026-09-10: first report
```

Rules:
- `symptom` is one line in the words a requester would use, plus the key error string if there is one. This is what recall matches on.
- `tags` carry resource names, tools and error fragments, lowercase.
- Update an existing episode when the symptom repeats: bump `last_seen` and `occurrences`, add an occurrences line, adjust the resolution if it changed.
- If a stored resolution proved wrong, fix it in place and note it under Why / how to apply.
- Redact per the core SKILL.md before writing.
- `source: backfilled` means seeded by setup or refresh from a channel thread. Only write one when the thread shows a confirmed resolution; otherwise use `outcome: unconfirmed`.
