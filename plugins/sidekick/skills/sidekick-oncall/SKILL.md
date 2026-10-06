---
name: sidekick-oncall
description: Monitors a Slack support channel for new requests addressed to the user and prepares for each one using the sidekick. Runs as a self-paced loop, each tick reads new messages since the cursor, recalls similar past episodes, drafts a reply as a Slack draft (never posts), queues questions when unsure, and keeps quiet when nothing is new. Use when the user says "go on call", "watch the support channel", "monitor #channel", "oncall sidekick", "triage new requests", or wants requests handled while they work.
---

# Sidekick oncall

Read `../sidekick/SKILL.md` for the request-handling flow and `../sidekick/references/state-files.md` for state. Oncall applies that flow to each new message in a loop. It never posts: the user sends everything, because a wrong message from a person's account is hard to undo.

## Start

1. Resolve the channel and check `profile.md` exists (else point to `sidekick-setup`). Load Slack tools with ToolSearch, including `slack_send_message_draft`.
2. Read `Who is asked` from the profile. This decides which messages are "ours". If it is empty or marked uncertain, ask the user once and do not guess.
3. Start the loop. In `/loop` dynamic mode use ScheduleWakeup each tick, passing the same prompt back. Suggest a delay of 5 minutes during working hours and 20-30 minutes otherwise, since the channel's real rate is low. Stop when the user says so.

## Each tick

1. Read messages newer than `cursor.last_ts` (`oldest` = cursor), top-level only first.
2. If there are none, call it a quiet tick: advance nothing, schedule the next wake with `noop: true`, and say nothing to the user.
3. For each new top-level message:
   - Not addressed to us per the profile: note as "not for us" in the tick summary, no draft.
   - Addressed to us: run the core flow steps 2-6 (classify, recall, decide, serve, flag uncertainty). Save the drafted reply with `slack_send_message_draft` as a thread reply, and give the user the one-line diagnosis plus the draft.
   - Include links or ids for anything the draft cites. Do not invent facts, run only read-only checks. Follow the core skill's live-context step for linked PRs and runs, and its rule on placeholders: if you did not verify something, the draft says so with a visible placeholder.
4. Advance the cursor to the newest message read.
5. Summarize the tick in at most a few lines: count of new requests, for each one the category, whether an episode matched, and whether a draft or a question was created. Schedule the next wake with `noop: false` if anything happened.

## Learning from outcomes

When the user later tells you a request is resolved, or a thread shows the fix confirmed, store the episode per core step 7. If the user corrects a draft, treat the correction as the truth: update the episode, and if it reflects a house rule, queue a question so it can be recorded as operator guidance.

## Boundaries

No posting, no mutating commands, no secrets in drafts or episodes. If Slack access fails, stop the loop and say why instead of retrying silently.
