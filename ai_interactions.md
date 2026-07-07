# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

"Draft a test plan for the most important edge cases in a pet scheduler with sorting and recurring tasks, then implement the suite in `tests/test_pawpal.py`. Include at least sorting correctness, recurrence logic, and conflict detection."

**What did the agent do?**

1. Read `pawpal_system.py` and the existing `tests/test_pawpal.py` to understand what was already implemented and already tested.
2. Proposed an 18-test plan grouped into four categories (sorting, recurrence, conflict detection, edge cases) and described each test in plain English before writing any code — this was a checkpoint I approved before it touched the file.
3. Wrote the full test suite and ran `pytest`.
4. One test — a task with `duration_minutes=0` — failed. The agent read the failure, traced it to `Scheduler._best_fit_subset()`'s subset-sum dedup logic (a zero-duration task can never make it into a combination because it never changes the running total, so it's silently dropped), and explained the root cause before proposing a fix.
5. After I redirected the fix (see Prompt Comparison below), it implemented the agreed-on fix, re-ran the full suite (`41 passed`), and updated the README's testing section with the real `pytest` output rather than a placeholder.

**What did you have to verify or fix manually?**

The agent's first proposed fix was architecturally reasonable but placed in the wrong layer — patching the scheduler's internal tie-breaking logic to special-case a zero-duration task, rather than rejecting that input where it's created. I caught this and asked for boundary validation instead. I also verified every test actually ran (not just that the agent claimed success) by checking the real `pytest` output myself, and manually exercised both `main.py` and the Streamlit UI afterward to confirm the same behaviors held up outside the test harness.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

Same model (Claude, Sonnet 5) and same underlying bug — the `duration_minutes=0` test failure in `Scheduler._best_fit_subset()` — but two different prompt framings, compared directly against each other.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude (Sonnet 5) | Claude (Sonnet 5) |
| **Prompt** | "The test failed, here's the traceback — fix it so the test passes." (implicit: fix wherever makes the failure go away) | "Why not just validate the input and reject `0` with a clear message, instead of fixing the scheduler algorithm?" (explicit: fix at the boundary, not internally) |
| **Response summary** | Patched `_best_fit_subset()`'s subset-sum dedup so that when two combinations reach the same total duration, it keeps whichever uses more tasks — a zero-duration task then always "wins" a tie and gets included. | Added a `Task.__post_init__` check that raises `ValueError` for any `duration_minutes < 1`, so the invalid state can never be constructed in the first place. |
| **What was useful** | Technically correct, and as a side effect also fixed an unrelated pre-existing quirk (ties in total duration were broken by first-seen-wins rather than most-tasks-completed). | Simple, one `if` statement; matches the constraint the Streamlit form (`min_value=1`) already enforces; the scheduler's algorithm is untouched. |
| **Problems noticed** | Added complexity to an already-subtle algorithm to handle an input (a real, zero-cost care task) that isn't a realistic scenario for this app — solving a problem at the wrong layer. | None — this is strictly the smaller, more targeted change. |
| **Decision** | Rejected. | Shipped. |

**Which approach did you use in your final implementation and why?**

Option B. The rule of thumb that decided it: validate at the boundary where invalid data could enter the system (object construction), rather than making every downstream consumer of that data defensively handle a state that should never exist. Option A's fix wasn't wrong, exactly — it was a legitimate generic improvement to the tie-breaking logic — but it solved the immediate bug by teaching the scheduler to tolerate bad input instead of preventing the bad input from existing, which is more code and more surface area for the same outcome.
