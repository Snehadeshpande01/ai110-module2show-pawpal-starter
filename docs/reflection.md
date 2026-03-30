# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

I designed four main classes: `Owner`, `Pet`, `Task`, and `Scheduler`.

- `Owner`: stores owner identity, availability, preferences, and owned pets. It is responsible for registering pets, tracking daily availability, and expressing task preferences.
- `Pet`: stores pet details, care requirements, preferences, and assigned tasks. It is responsible for describing pet needs and preferred activity times.
- `Task`: stores a care action with title, duration, priority, task type, preferred time, and the related pet. It is responsible for determining whether it is high priority, whether it fits a time window, and explaining why it was chosen.
- `Scheduler`: stores the owner, pets, task list, and scheduling constraints. It is responsible for ranking tasks, filtering them by constraints, selecting a daily task set, and generating explanations.

I also asked Copilot to review `#file:pawpal_system.py` for missing relationships or potential logic bottlenecks.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. I changed the `Task` class so it references a `Pet` object directly instead of storing only a pet name. I also added a `tasks` list to `Pet` and a `pets` list to `Scheduler` so the relationships between owner, pet, task, and scheduler are explicit. These changes make the model closer to the UML and reduce the risk of losing pet-task associations during scheduling.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints: task priority (high/medium/low), preferred time slot (morning/afternoon/evening), and a daily time budget (`max_daily_minutes`). It also detects conflicts when two tasks share the same time slot, and filters tasks against the owner's availability window using `fits_in_window()`.

Priority was treated as the most important constraint because a missed high-priority task (like feeding) has real consequences for the pet's wellbeing. Time slot preference comes second — it keeps the schedule aligned with the pet's natural routine. The daily budget acts as a hard cap that drops lower-priority tasks when time runs out.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler uses a greedy selection strategy in `select_tasks_for_day()`: it walks the ranked list in order and adds each task if it fits within the remaining daily minutes, stopping when the budget is exhausted. This means it never rearranges tasks to fit a shorter one in place of a longer one — a 30-minute walk blocks a later 10-minute feed even if swapping them would fit more total tasks.

This is a reasonable tradeoff for a pet care context because priority order should be respected over pure time efficiency. A pet owner would rather complete the high-priority walk and skip a low-priority grooming session than do the grooming first just because it is shorter. Simplicity also matters: the greedy approach is easy to understand, debug, and explain to a non-technical user.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
