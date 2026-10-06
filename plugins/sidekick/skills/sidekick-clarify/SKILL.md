---
name: sidekick-clarify
description: Lets the operator answer the questions the sidekick queued about a Slack support channel. Generates a local HTML page from the open questions (nothing hosted), the operator picks options or writes answers and exports a file, then the answers are merged into the channel profile as operator guidance that overrides inferred context. Use when the user says "clarify", "what do you need from me", "answer sidekick's questions", "sidekick has questions", or after setup, refresh or oncall report open questions.
---

# Sidekick clarify

Closing the gap between what the sidekick inferred and what the operator knows. Answers become operator guidance in `profile.md`, which wins over anything learned from the channel, so a short answer here beats many inferred patterns.

State layout: `../sidekick/references/state-files.md`. State dir: `${SIDEKICK_HOME:-~/.claude/sidekick}/<channel-slug>/`.

## Steps

1. **Render.** Set `SKILL_DIR` to this skill's base directory (the harness states it when the skill loads). Resolve the channel slug (ask if more than one channel has open questions and none was named), then:
   ```bash
   python3 "$SKILL_DIR/scripts/clarify.py" render "$STATE" --open
   ```
   It writes `clarify.html` into the state dir, prints the count of open questions, and opens the page. If the count is 0, say there is nothing to ask and stop. The page is a local file so internal details never leave the machine.
2. **Tell the user** to answer what they can, click Export, and say when done. Skipped questions stay open.
3. **Merge.** When they confirm:
   ```bash
   python3 "$SKILL_DIR/scripts/clarify.py" merge "$STATE"
   ```
   With no path it takes the newest `~/Downloads/answers*.json`. Pass a path if the user saved it elsewhere. It records the answers in `answers.json`, marks questions answered, and appends them under `## Operator guidance` in `profile.md`.
4. **Apply.** Read the merged guidance. If an answer changes how existing episodes should be read (for example a stored fix that the operator says is not allowed), update or delete those episodes, after listing them for the user to confirm.
5. **Report** how many answers were merged and how many questions remain open.

## Writing good questions

Other sidekick skills add questions, so keep them answerable in a few seconds: one decision per question, 2-4 concrete options plus free text, and a short redacted context line saying where the doubt came from. Do not ask what a tool or the channel history can answer.
