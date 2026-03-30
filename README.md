# PawPal+

A Python scheduling app that helps pet owners plan daily care tasks across multiple pets.

## Project Structure

```
pawpal_system/__init__.py   Core classes: Task, Pet, Owner, Scheduler
main.py                     Demo script — run this to see all features
app.py                      Streamlit web interface
tests/test_pawpal.py        Unit tests
docs/reflection.md          Design and reflection notes
```

## Quick Start

```bash
python main.py
```

## Core Classes

| Class | Responsibility |
|---|---|
| `Task` | A single care action with priority, duration, time slot, and recurrence |
| `Pet` | A pet with assigned tasks and time preferences |
| `Owner` | Owns pets, sets availability windows, holds scheduling preferences |
| `Scheduler` | Ranks, filters, and selects tasks for the day |

---

## Smarter Scheduling

The following features were added beyond the baseline to make the scheduler more useful for real pet care scenarios.

### Sort by Time Slot — `Scheduler.sort_by_time()`

Tasks are sorted chronologically by their `preferred_time` value using a lambda key and a lookup dict:

```
morning  →  afternoon  →  evening  →  (no preference)
```

This means the daily list always reads in the order the owner will actually do the tasks, not in the order they were entered.

```python
sorted_tasks = scheduler.sort_by_time()
```

---

### Filter by Pet or Status — `Scheduler.filter_tasks()`

Tasks can be filtered by completion status, pet name, or both at once:

```python
scheduler.filter_tasks(completed=False)            # pending only
scheduler.filter_tasks(pet_name="Mochi")           # one pet only
scheduler.filter_tasks(completed=True, pet_name="Luna")  # combined
```

Useful for checking what one pet still needs today, or reviewing what has already been done.

---

### Recurring Tasks — `Task.mark_completed()`

When a task with `frequency="daily"` or `frequency="weekly"` is marked complete, a new instance is automatically created for the next occurrence using `timedelta`:

```python
task = Task(title="Morning walk", duration_minutes=30,
            frequency="daily", due_date=date.today())
pet.add_task(task)
task.mark_completed()
# A new "Morning walk" task now exists on the pet, due tomorrow
```

| Frequency | Next due |
|---|---|
| `"daily"` | `due_date + timedelta(days=1)` |
| `"weekly"` | `due_date + timedelta(weeks=1)` |

The completed original is preserved for history. The new task inherits all fields (priority, duration, time slot, notes).

---

### Conflict Detection — `Scheduler.detect_conflicts()`

The scheduler checks for tasks that share the same time slot. Since the owner cannot attend to two pets at the same time, any two tasks in the same slot are flagged:

```python
warnings = scheduler.detect_conflicts()
for w in warnings:
    print(w)
# WARNING: 'Morning walk' (Mochi) and 'Morning brush' (Luna) are both
# scheduled in the morning slot — possible conflict.
```

Returns a list of warning strings — the program never crashes. An empty list means no conflicts were found.

---

### Skipped Task Visibility

Tasks dropped by the daily time budget can be surfaced explicitly by comparing the ranked list against the final selection:

```python
ranked   = scheduler.rank_tasks()
selected = scheduler.generate_schedule()
skipped  = [t for t in ranked if t not in selected]
```

---

## Running Tests

```bash
pytest tests/
```

---

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Category | # Tests | What is verified |
|---|---|---|
| **Sorting correctness** | 3 | `sort_by_time()` returns tasks in morning → afternoon → evening order; tasks with no `preferred_time` fall to the end; same-slot order is stable |
| **Recurrence logic** | 6 | Completing a `daily` task creates a new task due the next day; `weekly` advances by 7 days; missing `due_date` falls back to today; unknown frequencies (e.g. `"monthly"`) and non-recurring tasks do not spawn follow-ups; orphan tasks (no pet) do not crash |
| **Conflict detection** | 5 | Two tasks in the same slot produce a warning; different slots produce none; three tasks in one slot yield 3 pair-wise warnings; completed tasks are excluded; tasks without a `preferred_time` are never flagged |
| **Edge cases** | 4 | Pet with no tasks, owner with no pets, a task that exactly fills the daily budget (included), a task that exceeds it (excluded) |
| **Core behaviour** | 3 | Basic task addition, daily minute-limit scheduling, `describe_reason()` output |

**Total: 21 tests — all passing.**

### Confidence Level

**4 / 5 stars**

The core scheduling pipeline (ranking, filtering, daily-limit selection), recurring task logic, conflict detection, and time-slot sorting are all exercised across both happy paths and meaningful edge cases, giving strong confidence that the main features behave correctly. One star is held back because the tests do not yet cover the `fits_in_window` availability filtering in depth, multi-pet interactions with the full `generate_schedule()` pipeline, or the Streamlit UI layer (`app.py`).
