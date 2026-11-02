# Multi-Agent Code Review Pipeline

A hand-built multi-agent workflow for an AI coding assistant (Codex CLI). Five specialized agents check, fix, test, review and document a small Python project, and a custom MCP server streams every step to a live dashboard.

Built step by step as a practical assignment to learn how multi-agent systems work from the inside: roles, hand-offs, limits, loops and observability.

## How it works

```
Conductor -> Developer -> Tester -> Reviewer -> Documenter -> Conductor
                ^            |
                +-- FAIL ----+   (max 2 returns)
```

| Agent | Role | Can | Cannot |
|-------|------|-----|--------|
| Conductor | Plans the run (3-5 steps) and writes the final report | read | edit code |
| Developer | Fixes problems in `src/` according to the plan | read, edit | touch `tests/` |
| Tester | Writes and runs tests, returns PASS or FAIL | read, run | edit `src/` |
| Reviewer | Reviews the code and returns a table of remarks | read | edit anything |
| Documenter | Updates `README.md` after the review | read, edit | edit code |

Key rules (see `docs/workflow.md`):

- Each agent has a strict role, input, output and list of prohibitions (`agents/*.md`).
- If tests fail, the work goes back to the Developer at most 2 times. After that the run stops with the note "Tests did not pass after 2 iterations", so agents never loop forever and waste credits.
- Every run ends with a report in `reports/last-run.md`; lessons learned go to `docs/notes.md`.

## Commands

- `commands/check-project.md` - the full pipeline. Takes a folder as `$ARGUMENTS`, for example `src/`.
- `commands/quick-check.md` - Tester + Reviewer only, no code changes. Saves to `reports/quick-check.md`.

Run in Codex CLI from the project root:

```
Run the command from commands/check-project.md. Argument: src/
```

## Bonus: MCP server and live dashboard

`mcp/server.py` is a local MCP server (Python, FastMCP) with two tools:

- `report_step(agent, status, summary)` - each agent calls it at the start (`running`) and at the end (`done` or `failed`) of its work. The server saves the status to `.workflow/state.json`.
- `reset_run()` - clears the previous run.

`mcp/dashboard.py` serves `mcp/index.html` on `http://localhost:8765`. The page reads the state every second and shows:

- a block per agent, colored by status (gray waiting, yellow running, green done, red failed);
- a live event feed with timestamps;
- the Developer-Tester loop highlighted with a counter ("Return to Developer: N of 2");
- a reset button.

Data flow: agent -> `report_step` -> `server.py` -> `state.json` -> `dashboard.py` -> browser.

### Setup

```
pip install "mcp<2"
codex mcp add workflow -- python <path-to-project>/mcp/server.py
python mcp/dashboard.py
```

`mcp<2` is pinned on purpose: version 2.x renamed `FastMCP`, which breaks this server.

## The sample project: CLI task manager

`src/tasks.py` is a small console app used as the target for the agents. Tasks are stored in `src/tasks.json`.

```
python src/tasks.py add "Buy bread"
python src/tasks.py list
python src/tasks.py done 1
```

| Command | Action |
|---------|--------|
| `add <title>` | Adds a task. Empty or whitespace-only titles are rejected. |
| `list` | Shows all tasks (`[ ]` open, `[x]` done). |
| `done <id>` | Marks the task with the given ID as done. |

Successful commands exit with code `0`; bad arguments, unknown commands and missing IDs exit with code `1` and print the error to stderr.

Run the tests:

```
python -m unittest discover tests
```

Last run (2026-11-02): all 8 tests passed, no returns to the Developer were needed, review verdict OK, overall result PASS. Details in `reports/last-run.md`.

## Project structure

```
agents/      agent definitions (role, input, output, prohibitions)
commands/    check-project and quick-check commands
docs/        workflow.md (process rules) and notes.md (lessons learned)
mcp/         MCP server, dashboard server and HTML page
reports/     run reports
src/         sample Python task manager
tests/       unittest tests
```

## Tech

Codex CLI, Python 3.12, MCP (FastMCP), unittest, HTML/JavaScript, Git.

Author: [Oleksandr Melai](https://github.com/Wec3L)
