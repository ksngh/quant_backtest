# Codex Command Guide

# Purpose

This guide gives the project owner a consistent way to command Codex across coding, documentation, review, status, and planning requests.

The project rule remains unchanged: Codex must not make repository-changing implementation or documentation edits unless a specific task document is assigned or explicitly approved for creation.

# Command Types

## Answer-Only Request

Use this when you want an explanation, recommendation, or decision help and do not want file changes.

```text
Mode: answer only

Question:
<what you want to know>

Constraints:
- Do not edit files.
- Reference project rules if relevant.
```

Expected Codex behavior:

- Answer directly.
- Do not edit files.
- Do not require ledger/history reads unless they are needed for accuracy.
- If the answer recommends project changes, explain the required task document.

## Create Task Document

Use this when you have a raw requirement but no task file exists yet.

```text
Mode: create task

Goal:
<what the future task should accomplish>

Source requirement:
<raw requirement or notes>

Scope:
- <allowed area>

Out of scope:
- <forbidden area>

Acceptance criteria:
- <observable pass/fail result>

Verification:
- <command or manual review>
```

Expected Codex behavior:

- Read `AGENTS.md`, root `STATUS.md`, and relevant workflow docs.
- Read `BACKLOG.md` when selecting future candidate work to turn into a new task.
- Read `PROJECT_HISTORY.md` only when historical context is needed.
- Create or update only the task document and required status tracking.
- Do not implement application behavior unless the task is assigned for implementation.

## Coding Request

Use this when you want Codex to change application code.

```text
Task: tasks/<TASK_FILE>.md
Mode: implement

Goal:
<specific behavior to implement>

Scope:
- Allowed files or modules:
- Do not change:

Requirements:
- <required behavior>
- <required behavior>

Verification:
- <test command>

Completion:
Include files changed, implementation summary, tests added or updated, tests run, Codex self-review result, known limitations, and recommended next task.
```

Expected Codex behavior:

- Read `AGENTS.md`, root `STATUS.md`, relevant docs, and the assigned task file.
- Load area-relevant context only (backend vs frontend vs quant-core) by default.
- Do not load unrelated frontend/backend/core history by default.
- Use `PROJECT_HISTORY.md` only when historical context is relevant.
- Update `STATUS.md` when project state changes.
- Implement only the assigned task.
- Add or update tests when implementation changes behavior.
- Run verification when possible.
- Complete the Codex self-review before final response.

## Documentation Request

Use this when you want Codex to write or update project documents.

```text
Task: tasks/<TASK_FILE>.md
Mode: document

Goal:
<document change to make>

Allowed documents:
- <path>

Requirements:
- <content that must be included>
- <content that must remain unchanged>

Verification:
- git diff --check
```

Expected Codex behavior:

- Treat documentation changes as repository-changing work.
- Require the assigned task document.
- Keep changes limited to the requested documents and status updates.

## Review Request

Use this when you want Codex to inspect existing work without editing files by default.

```text
Mode: review

Review target:
<branch, diff, files, PR, or task>

Focus:
- scope expansion
- missing tests
- architecture boundaries
- safety rules

Output:
Findings first, ordered by severity, with file and line references where possible.
Do not edit files unless I explicitly assign a fix task.
```

Expected Codex behavior:

- Use code-review stance.
- Report bugs, regressions, missing tests, safety risks, and boundary violations first.
- Avoid edits unless a task is assigned for fixes.

## Status Or Verification Request

Use this when you want Codex to inspect state or run allowed checks.

```text
Mode: status

Request:
<what to inspect or verify>

Commands allowed:
- <command>

Do not edit files.
```

Expected Codex behavior:

- Read only the files or run only the commands needed.
- Summarize results.
- Do not edit files.

# Focused-Context Loading Rules

- `STATUS.md` is the active execution pointer, not a full history ledger.
- `PROJECT_HISTORY.md` is historical reference and should be loaded only when relevant to the assigned task.
- `BACKLOG.md` is for future/deferred candidate work and is not active execution state.
- Backend implementation requests should avoid unrelated frontend and quant-core history by default.
- Frontend implementation requests should avoid unrelated backend and quant-core history by default.


# Short Prompt Templates

## New Coding Task

```text
Task: tasks/<TASK_FILE>.md
Mode: implement

Implement the assigned task exactly as written.
Read `AGENTS.md`, `STATUS.md`, relevant docs, and the task file first.
Do not expand scope.
Run the required verification.
End with the required completion summary.
```

## New Documentation Task

```text
Task: tasks/<TASK_FILE>.md
Mode: document

Update only the assigned documentation.
Preserve existing project safety rules.
Run `git diff --check`.
End with the required completion summary.
```

## Create A Task Before Work

```text
Mode: create task

Create a task document for this requirement:
<raw requirement>

Do not implement yet.
Update `STATUS.md` only if project state changes.
```

## Review Without Editing

```text
Mode: review

Review the current diff against the assigned task.
Findings first, ordered by severity.
Do not edit files.
```

## Ask For Guidance

```text
Mode: answer only

Question:
<question>

Do not edit files.
```

# Consistency Rules For Codex

- If the user assigns `Task: tasks/<TASK_FILE>.md`, Codex treats that task as the active work item for the turn.
- If the user requests repository-changing coding or documentation without a task document, Codex stops and asks the project owner to assign or approve creation of a task.
- If the user requests answer-only help, Codex answers without requiring a task document.
- If the user request is unclear, Codex extracts assumptions and roles before implementation.
- If a request conflicts with `AGENTS.md`, `STATUS.md`, or the assigned task, Codex follows the stricter project rule and reports the conflict.
- Codex must not weaken safety rules for live trading, API keys, `.env` files, or exchange order endpoints.
- Codex must leave unrelated files alone.
