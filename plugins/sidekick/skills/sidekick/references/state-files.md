# Per-channel state

Root: `${SIDEKICK_HOME:-~/.claude/sidekick}/<channel-slug>/`

```
profile.md       learned channel context (setup writes, refresh updates, clarify adds operator guidance)
episodes/        one markdown file per resolved request (see episode-format.md)
questions.json   open and answered clarification questions
answers.json     operator answers exported from the clarify page
cursor.json      last processed Slack timestamp
```

## profile.md

```markdown
# <channel name> profile
channel_id: <id>
learned_from: <oldest date> to <newest date>, <n> requests
last_refreshed: <date>

## Purpose
One or two lines on what the channel is for.

## Who is asked
How requests are addressed (user group or person tags, keywords) so oncall can tell which messages are for us.

## Who responds
Roles of the people who normally answer, and what they usually own. No personal data beyond role.

## Categories
### <category-slug>
- description:
- signals: words, tools, error strings that identify it
- typical resolution: the usual shape of the fix, only if seen in threads
- first checks: what responders check first, only if seen
- confidence: high | medium | low

## Conventions
Tone, reply length, links and emoji habits, response-time norms, escalation paths, what is announced where.

## Tools and systems seen
Names only.

## Out of scope
Requests responders redirect elsewhere, and where.

## Unread threads
Threads setup or refresh could not read in full (thread timestamp, a few words). Refresh finishes these.

## Operator guidance
Answers from clarify. These win over everything inferred above.
```

Every claim in the profile must trace to something seen in the channel. If it was not seen, leave it out or ask a question.

## questions.json

```json
{
  "channel": "<slug>",
  "questions": [
    {
      "id": "q-001",
      "category": "access-grant",
      "question": "Who approves temporary production access?",
      "context": "Seen in 3 threads, approval came from different people each time. Examples: <short redacted quotes or thread ids>",
      "options": ["Team lead", "Requester's manager", "Depends on system"],
      "allow_free_text": true,
      "status": "open",
      "asked_at": "2026-10-06"
    }
  ]
}
```

Ask only what blocks a good answer. Prefer 2-4 options plus free text. Ids are `q-NNN`, never reused.

## answers.json

```json
{ "q-001": { "choice": "Depends on system", "text": "Prod needs lead approval, staging does not", "answered_at": "2026-10-06T10:00:00Z" } }
```

`clarify.py merge` moves answers into `profile.md` under Operator guidance and marks the questions `answered`.

## cursor.json

```json
{ "channel_id": "C0123", "last_ts": "1790000000.000100", "updated": "2026-10-06" }
```

Slack timestamps are strings. Compare them as numbers, never as text.
