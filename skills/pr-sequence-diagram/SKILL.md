---
name: pr-sequence-diagram
description: Emits a high-level Mermaid sequence diagram of the work done in a PR (diff vs. base branch) so a reader grasps the motive in 5-15 seconds. Use whenever the user wants to visualize a PR, see "what this branch does", or has invoked `/review` / `/security-review`. Trigger on phrases like "diagram this PR", "show the flow of these changes", "visualize the branch", "sequence diagram for the diff", "walk me through this branch", "what does this PR do", or any request to summarise a branch's behavior visually.
---

# PR Sequence Diagram

## Purpose

A reviewer opening a PR needs to understand the *motive* of the change in seconds — not line-by-line, but "user clicks X, which now also does Y before Z". A dense or exhaustive diagram defeats that purpose. This skill emits a one-glance Mermaid sequence diagram that captures the dominant flow the PR introduces or changes.

The diagram is a **summary artefact**, not a trace. It is OK — and expected — to omit most of the diff. Pick the flow that best explains why the PR exists.

## Inputs

- **Scope**: the diff of the current branch vs. its base branch. Determine the base branch in this order:
  1. If the user names one ("against main", "vs. develop"), use it.
  2. Else, use the branch's upstream merge-base if it exists (`git merge-base HEAD @{u}` — typically `main` or `master`).
  3. Else, fall back to `main`, then `master`.
- **Diff content**: `git diff <base>...HEAD` (three-dot = merge-base diff) plus `git log <base>..HEAD --oneline` for commit intent.
- **Remote PRs**: if the user gives a PR URL or number and `gh` is on PATH, use `gh pr view <n> [-R owner/repo] --json ...` and `gh pr diff <n> [-R owner/repo]`.

If there is no diff, stop and tell the user — there is nothing to diagram.

## Process

### 1. Read the change holistically

Answer: **what does this PR make the system do that it didn't before?** Look at:

- Commit messages and PR title/description.
- New or modified entry points: HTTP handlers, event subscribers, CLI commands, UI components, scheduled jobs.
- New calls *out*: API requests, DB queries, queue publishes, service calls, IAM role assumptions.
- Control-flow changes in existing entry points.

Ignore pure refactors, formatting, tests, dep bumps unless the whole PR is one of those — in which case, say so in the caption and pick the most meaningful flow anyway.

### 2. Pick participants (≤6, hard)

Smallest set that tells the story. Roles, not filenames. Good participants feel like a whiteboard sketch:

- `User`, `Browser`, `Mobile App`
- `API`, `Auth Service`, `Billing Service`
- `Postgres`, `Redis`, `Queue`
- Third parties: `Stripe`, `SendGrid`, `AWS STS`

If the PR touches one layer only (e.g., pure frontend), the grain can be finer: `User`, `LoginPage`, `useAuth hook`, `API`. Match grain to what the PR actually changes.

Drop candidates that appear in only one arrow before you hit the cap.

### 3. Pick arrows (≤10, hard)

Each arrow earns its place. Prefer arrows that are *new or changed* over arrows that already existed — one or two pre-existing arrows as anchors are fine if they orient the reader, but label them neutrally.

Prefer verbs and business nouns over method names. `submit order` > `POST /orders` > `handleOrderSubmit()`. The reader should understand intent without knowing the codebase.

`alt`/`opt` blocks are fine but spend them sparingly — every block eats into the glance budget.

### 4. Write the caption

Plain-English motive. One sentence, ~15-25 words. If it runs longer you're describing the **what**, not the **why** — compress. Not a commit-message rehash. Examples:

- "Adds a Stripe webhook path so subscription cancellations from the Stripe dashboard propagate back into our billing state."
- "Moves password-reset email sending off the request path and onto a background queue."
- "Introduces a feature-flag check before the new onboarding flow so we can dark-launch it."

If you can't write this sentence confidently from the diff, re-read the diff; don't guess.

### 5. Emit the artefact

Output the caption followed by a Mermaid sequence-diagram code fence:

```
<H2 or H3 heading — PR title or "What this PR does">

<one-sentence motive caption>

```mermaid
sequenceDiagram
    participant U as User
    participant API
    participant DB as Postgres
    U->>API: submit order
    API->>DB: insert order row
    API-->>U: 201 Created
\```

<optional: 1-3 short bullets below the diagram for flows that didn't fit,
 e.g. error paths, legacy fallback, staged rollout. Skip if not needed.>
```

That's the whole artefact. Don't also write it to a file — whatever invoked the skill (a `/review` command, a free-form question) decides where the artefact lands in the larger response.

## Design constraints (hard)

- **≤6 participants**
- **≤10 arrows**
- **One-sentence caption**, ~15-25 words (plain English, describes the *why*)
- **No filenames or method signatures** in arrow labels — verbs and business nouns only

If the diff genuinely can't be compressed to these limits without losing meaning, pick the dominant flow and note in one line *below the diagram* that other flows were omitted. Don't produce a sprawling diagram "to be thorough" — that defeats the glance-budget.

## Mermaid syntax reminders

- `participant X as Display Name` when the short name differs from the label.
- `->>` synchronous call/request, `-->>` response/async reply.
- `Note over X,Y: text` for brief annotations — sparingly.
- Avoid activation bars (`->>+` / `-->>-`) unless a call's lifetime is the point of the story — they add ink without adding meaning in most sketches.
- At most one `alt`/`opt`/`loop`/`par` block per diagram — every block eats the glance budget. If you need more than one, your flow is too complex for a summary diagram; compress or pick a narrower slice.

## Edge cases

- **Very large PR**: pick the single most important flow; say so in the caption ("This PR also refactors X; diagram focuses on the new Y flow.").
- **Pure refactor / test-only PR**: say so in one sentence and skip the diagram — don't draw a trivial arrow to feel complete. Example: "This PR refactors `<area>` with no runtime behavior change; no sequence diagram applies."
- **Two PRs in a trenchcoat**: diagram the primary flow, mention the secondary briefly.
- **No base branch / detached HEAD**: tell the user and stop.
