---
name: sidekick-refresh
description: Lightweight update of a Slack support channel's sidekick profile and episodes using only messages since the saved cursor. Adds new categories, adjusts confidence and conventions, seeds new episodes from newly confirmed threads, and queues new questions. Use when the user says "refresh sidekick", "update the channel profile", "catch sidekick up", or after a long gap since setup or oncall, so the profile does not go stale.
---

# Sidekick refresh

An incremental setup. Read `../sidekick/references/state-files.md` and `../sidekick/references/episode-format.md`, and follow the learning steps in `../sidekick-setup/SKILL.md`, but limited to what is new.

## Steps

1. Load `profile.md` and `cursor.json`. If there is no profile, say so and point to `sidekick-setup`.
2. Finish any threads listed under `## Unread threads` in the profile first (large ones one at a time with `limit` and `cursor`), then remove the ones you completed from that section.
3. Read messages newer than `cursor.last_ts` with `slack_read_channel` (`oldest` = the cursor), paging as needed. Read threads for requests that now have replies, plus threads of earlier requests that were still open at the last refresh.
3. Update `profile.md` in place:
   - New request clusters become new categories, otherwise raise or lower confidence on existing ones.
   - Update conventions only when the new data clearly shows a change.
   - Never edit the Operator guidance section. If new data contradicts it, queue a question that quotes the guidance and the contradicting evidence.
4. Seed or update episodes by the same rules as setup. A repeated symptom updates the existing episode.
5. Queue new questions, skipping any already open or answered.
6. Advance the cursor and set `last_refreshed`.
7. Report what changed: new categories, changed confidence, episodes added or updated, new questions.
