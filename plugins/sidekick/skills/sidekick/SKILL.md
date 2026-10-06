---
name: sidekick
description: Core of the Slack support-channel sidekick. Handles one support request using what was learned about its channel: classify it, recall similar past episodes from the local store, serve it fresh if unseen, then store the outcome. Also provides status, forget and remember commands for the episode store. Use whenever the user pastes or links a request from a support channel, asks "have we seen this before", "how did we handle this", "sidekick status", "forget that episode", or "remember this resolution", even if they do not say "sidekick". For first-time channel learning use sidekick-setup, for monitoring use sidekick-oncall, for open questions use sidekick-clarify.
---

# Sidekick core

The sidekick learns one Slack support channel at a time and carries no channel knowledge of its own. Everything it knows lives in per-channel state, so it works for any support channel.

## State

Root: `${SIDEKICK_HOME:-~/.claude/sidekick}/<channel-slug>/` where the slug is the channel name (fall back to the channel id). Files and schemas are in `references/state-files.md`; the episode template is in `references/episode-format.md`.

If the channel has no `profile.md`, stop and tell the user to run `sidekick-setup <channel>` first. Guessing a channel's norms is how wrong answers get sent.

Slack tools are deferred. Load what you need with ToolSearch, for example `select:mcp__plugin_slack_slack__slack_read_channel,mcp__plugin_slack_slack__slack_read_thread,mcp__plugin_slack_slack__slack_send_message_draft`.

Draft only. Replies, commands and comments are drafted for the user. Run only read-only commands yourself. Anything that changes infrastructure, grants access, or posts to Slack or other external systems needs the user's explicit go-ahead in this conversation. Slack drafts are fine because the user sends them.

## Handle a request

1. **Read the profile.** Load `profile.md`. Operator guidance in it overrides anything inferred.
2. **Classify** into one of the profile's categories, or `other` and say so.
3. **Gather live context.** If the request links or names something with live state (a pull request, CI run, ticket, workspace, job), read it with read-only tools before answering, since stored episodes and the request text can be stale or thin. For a pull request: check its CI and check results, and if any are failing do a quick first investigation of why (read the failing job's log tail, say whether it looks like the change, a flake, or an infra problem). Also load the repository's agent and contribution rules if present (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `CONTRIBUTING.md`) and review against them. Report what you could not read instead of guessing.
4. **Recall.** Extract distinctive strings (error fragments, resource names, ticket ids) and search the episodes:
   ```bash
   grep -rilE "<string1>|<string2>" "$STATE/episodes/"
   grep -rl "category: <category>" "$STATE/episodes/"
   ```
   Read the best 1-3 matches fully. Match on symptom and tags first, category second.
5. **Decide.**
   - *Strong match* (same symptom and same system): apply the stored resolution, cite the episode file and its date, and re-verify anything time-sensitive (permissions, retention windows, versions, prices) against the live system, because episodes record what was true then.
   - *Weak match*: use it as a lead, say it is partial, and handle fresh.
   - *No match*: handle fresh with the real tools available. Do not guess facts a tool can tell you.
6. **Serve.** Answer first: diagnosis, then the drafted reply or command, in the channel's learned tone. Short, no preamble. Draft only what you verified: where a fact is unknown (PR state, who approves, whether a fix worked), leave a visible placeholder like `[status?]` for the user to fill. Do not draft an approval or a "fixed" message for something you have not actually checked.
7. **Flag uncertainty.** If a recalled episode has no recorded fix, queue one question asking how it is resolved, unless one is already open. If you could not decide something that depends on the operator's judgment or on house rules (who approves, what is allowed, which environment), add a question to `questions.json` instead of guessing, and tell the user one has been queued for `sidekick-clarify`.
8. **Store.** Once the user confirms the outcome, write or update an episode. Skip requests where nothing non-obvious was learned. Search for an existing episode with the same symptom first and update it rather than duplicating: bump `last_seen` and `occurrences`, append an occurrence line.

## Redaction (before every write)

Episodes are plain text on disk, so write only what is safe to keep.
- Never store secrets, tokens, keys, passwords or secret values. Store the name of the secret and where it lives.
- No customer names or personal data. Use generic wording.
- Requester names are not needed. Use roles or team names.
- Shorten URLs to the identifying part (run id, PR number, resource name).

## status

Count episodes by category, list the newest 5, the open question count, the cursor position, and any episode with `outcome: unconfirmed`. Report only what the files show.

## forget `<query>`

List matching episode files with a one-line summary of each, wait for the user to confirm, then delete only those. Verify the files are gone before saying so. Never delete before confirmation.

## remember `<fact>`

Write an episode from what the user states. Mark `source: user-stated` and `outcome: unconfirmed` unless they say it was verified. Redact first.

## Why it works this way

Stored resolutions go stale, so recall informs the answer and the live system confirms it. Plain files keep everything on the user's machine and inspectable. If wording differences make recall miss, a graph or vector layer can replace step 3 without changing the episode files.
