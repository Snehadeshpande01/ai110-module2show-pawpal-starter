import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import date, timedelta
from tabulate import tabulate
from colorama import init, Fore, Style

from pawpal_system import Owner, Pet, Task, Scheduler

init(autoreset=True)  # colorama: auto-reset color after each print

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

TASK_TYPE_EMOJI = {
    "walk":  "🦮",
    "feed":  "🍖",
    "play":  "🎾",
    "groom": "✂️ ",
    "vet":   "💉",
    "other": "📋",
}

PRIORITY_COLOR = {
    "high":   Fore.RED,
    "medium": Fore.YELLOW,
    "low":    Fore.GREEN,
}

SLOT_EMOJI = {
    "morning":   "🌅",
    "afternoon": "☀️ ",
    "evening":   "🌙",
}


def _priority_label(priority: str) -> str:
    color = PRIORITY_COLOR.get(priority.lower(), "")
    return f"{color}{priority.upper()}{Style.RESET_ALL}"


def _status_label(completed: bool) -> str:
    return f"{Fore.GREEN}DONE{Style.RESET_ALL}" if completed else f"{Fore.CYAN}PENDING{Style.RESET_ALL}"


def _type_emoji(task_type: str | None) -> str:
    return TASK_TYPE_EMOJI.get(task_type or "", "📋")


def _slot_label(preferred_time: str | None) -> str:
    if not preferred_time:
        return "(any)"
    emoji = SLOT_EMOJI.get(preferred_time.lower(), "")
    return f"{emoji} {preferred_time}"


def print_section(title: str) -> None:
    width = 62
    print()
    print(Fore.CYAN + Style.BRIGHT + "=" * width)
    print(f"  {title}")
    print("=" * width + Style.RESET_ALL)


def print_task_table(tasks: list[Task], title: str = "") -> None:
    if title:
        print_section(title)
    if not tasks:
        print(Fore.YELLOW + "  (no tasks)" + Style.RESET_ALL)
        return

    rows = []
    for t in tasks:
        pet_name = t.pet.name if t.pet else "—"
        freq = f"[{t.frequency}]" if t.frequency else ""
        due = str(t.due_date) if t.due_date else ""
        rows.append([
            f"{_type_emoji(t.task_type)} {t.title}",
            pet_name,
            _priority_label(t.priority),
            _slot_label(t.preferred_time),
            f"{t.duration_minutes} min",
            freq,
            due,
            _status_label(t.completed),
        ])

    headers = ["Task", "Pet", "Priority", "Time Slot", "Duration", "Recurs", "Due", "Status"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=2)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    # Tasks added OUT OF ORDER (evening first, then morning tasks)
    task1 = Task(title="Evening play",    duration_minutes=20, priority="low",
                 task_type="play",  preferred_time="evening",   frequency="weekly", due_date=today)
    task2 = Task(title="Afternoon groom", duration_minutes=15, priority="medium",
                 task_type="groom", preferred_time="afternoon")
    task3 = Task(title="Morning walk",    duration_minutes=30, priority="high",
                 task_type="walk",  preferred_time="morning",   frequency="daily",  due_date=today)
    task4 = Task(title="Feed breakfast",  duration_minutes=10, priority="medium",
                 task_type="feed",  preferred_time="morning")

    # Deliberate conflict: same morning slot, different pet
    task5 = Task(title="Morning brush",   duration_minutes=10, priority="medium",
                 task_type="groom", preferred_time="morning")

    luna.add_task(task5)
    luna.add_task(task1)
    mochi.add_task(task2)
    mochi.add_task(task3)
    mochi.add_task(task4)

    scheduler = Scheduler(owner=owner, constraints={"max_daily_minutes": "120"})

    # --- Sorted by time ---
    print_task_table(scheduler.sort_by_time(), "All Tasks — Sorted by Time Slot")

    # --- Filter by pet ---
    print_task_table(scheduler.filter_tasks(pet_name="Mochi"), "Mochi's Tasks Only")

    # --- Conflict detection ---
    print_section("Conflict Detection")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(Fore.RED + "  ⚠  " + warning + Style.RESET_ALL)
    else:
        print(Fore.GREEN + "  No conflicts detected." + Style.RESET_ALL)

    # --- Mark recurring tasks complete ---
    print_section(f"Marking Recurring Tasks Complete  (today = {today})")
    task3.mark_completed()
    task1.mark_completed()
    print(Fore.GREEN + f"  DONE  Morning walk (daily)   — next due: {today + timedelta(days=1)}" + Style.RESET_ALL)
    print(Fore.GREEN + f"  DONE  Evening play (weekly)  — next due: {today + timedelta(weeks=1)}" + Style.RESET_ALL)

    # --- Pending tasks (includes auto-created recurrences) ---
    print_task_table(scheduler.filter_tasks(completed=False),
                     "Pending Tasks — Includes Auto-Created Recurrences")

    # --- Completed tasks ---
    print_task_table(scheduler.filter_tasks(completed=True), "Completed Tasks")

    # --- Today's generated schedule ---
    print_section("Today's Generated Schedule")
    schedule = scheduler.generate_schedule()
    ranked   = scheduler.rank_tasks()
    skipped  = [t for t in ranked if t not in schedule and not t.completed]

    if schedule:
        total = sum(t.duration_minutes for t in schedule)
        print(Fore.CYAN + f"  {len(schedule)} task(s) scheduled  |  {total} / 120 minutes used\n" + Style.RESET_ALL)
        rows = []
        for t in schedule:
            rows.append([
                f"{_type_emoji(t.task_type)} {t.title}",
                t.pet.name if t.pet else "—",
                _priority_label(t.priority),
                _slot_label(t.preferred_time),
                f"{t.duration_minutes} min",
                scheduler.explain_choice(t),
            ])
        headers = ["Task", "Pet", "Priority", "Time Slot", "Duration", "Reason"]
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))

    if skipped:
        print(Fore.YELLOW + f"\n  Skipped ({len(skipped)} over budget):" + Style.RESET_ALL)
        for t in skipped:
            print(Fore.YELLOW + f"    - {_type_emoji(t.task_type)} {t.title} "
                  f"({t.pet.name if t.pet else '?'}) — {t.duration_minutes} min, {t.priority}" + Style.RESET_ALL)
    print()
