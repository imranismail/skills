---
name: sidekick-setup
description: First-time learning of a Slack support channel for the sidekick. Scans the channel history and threads, clusters requests into categories, learns who is asked, who responds, tone and conventions, seeds episodes from threads with confirmed resolutions, and queues questions about anything it cannot determine. Use when the user says "set up sidekick for #channel", "learn this support channel", "scan this channel", gives a Slack channel link or id to onboard, or when sidekick reports a channel has no profile. Works for any support channel, nothing channel-specific is built in.
---

# Sidekick setup

Build the initial context for one channel from what is actually in it. The channel is the only source of truth: a category, norm or fix that was not seen in the history does not go in the profile. Where the history is ambiguous, ask instead of guessing; wrong confident context is worse than an open question.

Read `../sidekick/references/state-files.md` and `../sidekick/references/episode-format.md` first.

## Steps

1. **Resolve the channel.** Accept a Slack URL, channel id or name. Load Slack tools with ToolSearch (`slack_read_channel`, `slack_read_thread`, `slack_search_channels`). The slug is the channel name. If `$STATE/profile.md` exists, tell the user and suggest `sidekick-refresh`, and stop unless they ask to rebuild.
2. **Read history.** Page through `slack_read_channel` (100 per page, use `cursor`) back about 3 months or 500 top-level messages, whichever comes first. Use `response_format: concise` first. Note which messages have threads.
3. **Read threads.** Read threads for a sample that covers every cluster, at least the 30 most recent threaded requests and any that look like repeats. Resolutions live in threads. Use `slack_read_thread`. Tool output can be truncated on long threads: read the biggest threads one at a time with a `limit`, paging with `cursor`. List any thread you could not read in full under a `## Unread threads` section of the profile (thread timestamp and a few words), so a later refresh can finish them.
4. **Learn the channel.** From the messages:
   - *Who is asked*: the tag, user group or keyword most requests carry.
   - *Who responds*: roles and what they own, from who answers what.
   - *Categories*: cluster requests by what is being asked. Name each with a short slug, record signals (words, tools, error strings), the typical resolution and first checks only if responders showed them, and a confidence level. Merge clusters under about 3 occurrences into `other` unless they are clearly distinct.
   - *Conventions*: tone, reply length, link habits, escalation, response times.
   - *Out of scope*: requests responders redirected elsewhere.
5. **Write `profile.md`** per the schema. Redact as in the core skill. No personal names, use roles.
6. **Seed episodes.** Seed one episode per distinct symptom seen in a thread, because recall can only say "seen before" for symptoms that were written down.
   - Confirmed fix visible (responder says done, requester says thanks or it works): `source: backfilled`, `outcome: resolved`, with the steps.
   - Likely fix but no confirmation: `outcome: unconfirmed`.
   - Symptom and responder role seen but the fix is not in the thread: still write it, `outcome: unconfirmed`, Resolution says "fix not recorded in thread" plus who resolved it by role and the thread timestamp, and queue one question asking how it is resolved. Never invent steps.
   - Skip only routine requests with nothing to learn (bare "please review" posts, thank-you messages). Check for duplicates by symptom before writing.
7. **Queue questions.** Add to `questions.json` anything that would change how requests are handled and was not clear: unclear approvers, undocumented rules, categories with low confidence, conflicting resolutions for the same symptom, requests that were never answered. Two to four options plus free text. Keep it to the 5-10 that matter most.
8. **Set the cursor** to the newest message timestamp read, as a string.
9. **Report** in a few lines: channel, window and message count, categories found with counts, episodes seeded, open questions. Point to `sidekick-clarify` if there are questions and `sidekick-oncall` for monitoring.

## Boundaries

Read-only against Slack. Never post. Never store secret values seen in messages, only their names. If the channel is private and the tools cannot read it, say so and stop.
