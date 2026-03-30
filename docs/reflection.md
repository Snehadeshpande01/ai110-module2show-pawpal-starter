# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed four main classes: `Owner`, `Pet`, `Task`, and `Scheduler`.

- `Owner`: stores owner identity, availability, preferences, and owned pets. It is responsible for registering pets, tracking daily availability, and expressing task preferences.
- `Pet`: stores pet details, care requirements, preferences, and assigned tasks. It is responsible for describing pet needs and preferred activity times.
- `Task`: stores a care action with title, duration, priority, task type, preferred time, and the related pet. It is responsible for determining whether it is high priority, whether it fits a time window, and explaining why it was chosen.
- `Scheduler`: stores the owner and scheduling constraints. It is responsible for ranking tasks, filtering them by constraints, selecting a daily task set, and generating explanations.

**b. Design changes**

Yes. Three significant changes happened during implementation:

1. **`Task` gained a `pet` back-reference and recurrence fields.** The initial design stored only a pet name string. During build it became clear that `mark_completed()` needed to call `pet.add_task()` directly to spawn the next occurrence, which required a proper object reference. `frequency`, `due_date`, `completed`, and `notes` were added to support recurring tasks and completion tracking.

2. **`Pet` gained a `tasks` list and `add_task()` / `pending_tasks()` methods.** The initial UML showed `Pet` as a passive data holder. In the final design, `Pet` owns its task list — this is the correct place for that relationship because a task belongs to exactly one pet and the pet's `add_task()` method sets the back-reference on the task at the same time.

3. **`Scheduler` lost the `pet` and `task_list` fields and gained four new methods.** The original diagram showed `Scheduler` holding its own copies of pets and tasks, which duplicated what `Owner` already tracked. The final design has `Scheduler` hold only `owner` and derive all tasks through `owner.all_tasks()` and `owner.pending_tasks()`. The new methods `sort_by_time()`, `filter_tasks()`, and `detect_conflicts()` were added to make the scheduler genuinely useful beyond a simple greedy selection.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: task priority (high/medium/low), preferred time slot (morning/afternoon/evening), and a daily time budget (`max_daily_minutes`). It also detects conflicts when two tasks share the same time slot, and filters tasks against the owner's availability window using `fits_in_window()`.

Priority was treated as the most important constraint because a missed high-priority task (like feeding) has real consequences for the pet's wellbeing. Time slot preference comes second — it keeps the schedule aligned with the pet's natural routine. The daily budget acts as a hard cap that drops lower-priority tasks when time runs out.

**b. Tradeoffs**

The scheduler uses a greedy selection strategy in `select_tasks_for_day()`: it walks the ranked list in order and adds each task if it fits within the remaining daily minutes, stopping when the budget is exhausted. This means it never rearranges tasks to fit a shorter one in place of a longer one — a 30-minute walk blocks a later 10-minute feed even if swapping them would fit more total tasks.

This is a reasonable tradeoff for a pet care context because priority order should be respected over pure time efficiency. A pet owner would rather complete the high-priority walk and skip a low-priority grooming session than do the grooming first just because it is shorter. Simplicity also matters: the greedy approach is easy to understand, debug, and explain to a non-technical user.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used at three distinct stages:

- **Design brainstorming:** I described the scheduling scenario in plain English and asked the AI to suggest which classes and relationships made sense before writing any code. This helped me identify the `Owner → Pet → Task` ownership chain early and avoid putting everything in a single flat list.
- **Debugging:** When `mark_completed()` was spawning duplicate tasks, I pasted the method and asked the AI to trace the execution path. It spotted that the `pet` back-reference was `None` in the test case because the task had been created outside `pet.add_task()`.
- **Test coverage:** After writing the core logic I asked the AI to list edge cases I might have missed. It identified the "orphan recurring task (pet=None)" and "unknown frequency" scenarios, both of which became explicit tests.

The most useful prompt pattern was: *"Given this method signature and docstring, what inputs would cause it to behave unexpectedly?"* This consistently surfaced boundary conditions that happy-path thinking misses.

**b. Judgment and verification**

The AI initially suggested that `Scheduler` should hold its own copy of the task list (mirroring the original UML). I did not accept this because it would mean the scheduler's list could go stale whenever a task was added to a pet after the scheduler was constructed. Instead I kept `Scheduler` referencing `owner` and deriving tasks dynamically through `owner.all_tasks()`. I verified this was correct by writing a test that adds a task after the scheduler is created and confirming `generate_schedule()` still sees it.

---

## 4. Testing and Verification

**a. What you tested**

The 21-test suite covers four main areas:

- **Sorting:** `sort_by_time()` returns tasks in morning → afternoon → evening order; tasks with no `preferred_time` fall to the end; tasks in the same slot maintain stable relative order.
- **Recurrence:** `mark_completed()` spawns a next-day task for `"daily"` frequency and a next-week task for `"weekly"`; a missing `due_date` defaults to `date.today()`; unknown frequencies (e.g. `"monthly"`) and tasks with `pet=None` exit cleanly without spawning or crashing.
- **Conflict detection:** Two tasks in the same slot produce exactly one warning; three tasks produce three pair-wise warnings; different slots produce no warnings; completed tasks are excluded; tasks with no `preferred_time` are skipped.
- **Edge cases / boundaries:** Owner with no pets, pet with no tasks, a task whose duration exactly equals the daily budget (must be included), a task that exceeds the budget alone (must be excluded).

These tests matter because the greedy scheduler and recurrence logic both have boundary conditions at zero and at exact equality that are easy to get wrong — the `<=` vs `<` check in `select_tasks_for_day()` is a single character that changes which tasks make it into the schedule.

**b. Confidence**

**4 / 5.** The core pipeline is well-covered. The remaining uncertainty is in:

- `fits_in_window()` with real time strings — only malformed-input fallback is implicitly tested.
- Multi-pet `generate_schedule()` scenarios where pets have overlapping priorities and time slots.
- The Streamlit UI — session state interactions and widget flows are not covered by any automated test.

If I had more time, the next tests would be: (1) an owner with two pets whose tasks compete for the same budget slot, and (2) a sequence of `mark_completed()` calls across several days to verify the recurrence chain stays consistent over multiple cycles.

---

## 5. Reflection

**a. What went well**

The relationship between `Pet` and `Task` turned out cleaner than I expected. Having `add_task()` set the back-reference (`task.pet = self`) in one place meant that every other method — `mark_completed()`, `describe_reason()`, `detect_conflicts()` — could always assume `task.pet` was populated correctly without defensive null checks scattered everywhere. That single design decision made the recurrence logic straightforward to implement and test.

**b. What you would improve**

The greedy daily selection algorithm is the weakest part of the design. A smarter approach would use a bounded knapsack algorithm to maximise the number of tasks (or total priority score) within the time budget rather than stopping at the first item that doesn't fit. I would also move the "skipped task" reporting into the `Scheduler` class itself rather than computing it in the UI layer, so it is testable independently of Streamlit.

**c. Key takeaway**

The most important thing I learned is that AI is most useful as a *question generator*, not an answer provider. Asking "what could go wrong with this method?" consistently surfaced better test cases than trying to think of them myself. But the AI's structural suggestions (like keeping a duplicate task list in the Scheduler) needed to be evaluated against the actual data flow of the system before accepting them. The skill is knowing when to use the suggestion as a starting point and when to push back.
