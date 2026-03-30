from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from itertools import combinations
from typing import List, Optional, Dict


def parse_time_stamp(value: str) -> time:
    """Parse a simple HH:MM time string into a time object."""
    return datetime.strptime(value, "%H:%M").time()


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"
    task_type: Optional[str] = None
    pet: Optional[Pet] = field(default=None, compare=False, repr=False)
    preferred_time: Optional[str] = None
    frequency: Optional[str] = None
    completed: bool = False
    notes: Optional[str] = None
    due_date: Optional[date] = None

    def mark_completed(self) -> None:
        """Mark this task as completed and schedule the next occurrence for recurring tasks."""
        self.completed = True

        if self.frequency is None or self.pet is None:
            return

        freq = self.frequency.lower()
        base = self.due_date if self.due_date else date.today()

        _FREQUENCY_DELTA = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
        delta = _FREQUENCY_DELTA.get(freq)
        if delta is None:
            return
        next_due = base + delta

        next_task = Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            task_type=self.task_type,
            preferred_time=self.preferred_time,
            frequency=self.frequency,
            notes=self.notes,
            due_date=next_due,
        )
        self.pet.add_task(next_task)

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority.lower() == "high"

    def fits_in_window(self, window: Dict[str, str]) -> bool:
        """Return True if the task fits within a given time window."""
        if not self.preferred_time or "start" not in window or "end" not in window:
            return True

        try:
            start_window = parse_time_stamp(window["start"])
            end_window = parse_time_stamp(window["end"])
        except ValueError:
            return True

        _SLOT_WINDOWS = {
            "morning":   (time(8, 0),  time(12, 0)),
            "am":        (time(8, 0),  time(12, 0)),
            "a.m.":      (time(8, 0),  time(12, 0)),
            "afternoon": (time(12, 0), time(18, 0)),
            "pm":        (time(12, 0), time(18, 0)),
            "p.m.":      (time(12, 0), time(18, 0)),
            "evening":   (time(17, 0), time(22, 0)),
            "night":     (time(17, 0), time(22, 0)),
        }
        slot = _SLOT_WINDOWS.get(self.preferred_time.lower())
        if slot is None:
            return True
        slot_start, slot_end = slot
        return start_window <= slot_end and end_window >= slot_start

    def describe_reason(self) -> str:
        """Return a short explanation for why this task is important."""
        pet_name = self.pet.name if self.pet else "the pet"
        return (
            f"{self.title} for {pet_name} is a {self.priority} priority task "
            f"and takes {self.duration_minutes} minutes."
        )


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    care_requirements: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet."""
        task.pet = self
        self.tasks.append(task)

    def needs_care(self) -> List[str]:
        """Return titles of pending care tasks for this pet."""
        return [task.title for task in self.tasks if not task.completed]

    def preferred_activity_times(self) -> List[str]:
        """Return the pet's preferred activity times."""
        times = self.preferences.get("preferred_times")
        if isinstance(times, list):
            return times
        if isinstance(times, str):
            return [times]
        return ["morning", "evening"]

    def describe(self) -> str:
        """Return a brief description of this pet."""
        age_description = f"{self.age}-year-old" if self.age is not None else "unknown-age"
        return f"{self.name} is a {age_description} {self.species}."

    def pending_tasks(self) -> List[Task]:
        """Return pending tasks for this pet."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    name: str
    availability: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet for this owner."""
        self.pets.append(pet)

    def set_availability(self, availability: Dict[str, str]) -> None:
        """Set the owner's available time windows."""
        self.availability = availability

    def prefers_task_type(self, task_type: str) -> bool:
        """Return True if the owner prefers the given task type."""
        task_order = self.preferences.get("task_order")
        if isinstance(task_order, list):
            return task_type in task_order
        return False

    def summary(self) -> str:
        """Return a short summary of the owner and their pets."""
        pet_names = ", ".join(pet.name for pet in self.pets) or "no pets"
        return f"{self.name} owns {pet_names}."

    def all_tasks(self) -> List[Task]:
        """Return all tasks across every pet owned by this owner."""
        return [task for pet in self.pets for task in pet.tasks]

    def pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks across every pet."""
        return [task for task in self.all_tasks() if not task.completed]


@dataclass
class Scheduler:
    owner: Owner
    constraints: Dict[str, str] = field(default_factory=dict)

    def generate_schedule(self) -> List[Task]:
        """Generate a daily schedule from the owner's pending tasks."""
        tasks = self.owner.pending_tasks()
        tasks = self.rank_tasks(tasks)
        tasks = self.filter_tasks_by_constraints(tasks)
        return self.select_tasks_for_day(tasks)

    def rank_tasks(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Rank tasks by priority, duration, and title."""
        if tasks is None:
            tasks = self.owner.all_tasks()

        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            tasks,
            key=lambda task: (
                priority_order.get(task.priority.lower(), 1),
                task.duration_minutes,
                task.title,
            ),
        )

    def filter_tasks_by_constraints(self, tasks: List[Task]) -> List[Task]:
        """Filter tasks to those that fit the owner's availability."""
        if not self.owner.availability:
            return tasks
        return [task for task in tasks if task.fits_in_window(self.owner.availability)]

    def select_tasks_for_day(self, tasks: List[Task]) -> List[Task]:
        """Select tasks for the day within the configured daily limit."""
        max_minutes = int(self.constraints.get("max_daily_minutes", 480))
        selected: List[Task] = []
        total = 0
        for task in tasks:
            if total + task.duration_minutes <= max_minutes:
                selected.append(task)
                total += task.duration_minutes
        return selected

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks chronologically by preferred time slot.

        Uses a lambda with a TIME_ORDER lookup dict as the sort key so that
        tasks are ordered morning -> afternoon -> evening.  Tasks with no
        preferred_time value fall to the end of the list (key = 99).

        Args:
            tasks: List of tasks to sort. Defaults to all tasks for this owner.

        Returns:
            A new list sorted by time slot, earliest first.
        """
        TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}
        if tasks is None:
            tasks = self.owner.all_tasks()
        return sorted(tasks, key=lambda t: TIME_ORDER.get(
            (t.preferred_time or "").lower(), 99
        ))

    def filter_tasks(
        self,
        tasks: Optional[List[Task]] = None,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by completion status and/or pet name.

        Each filter is applied only when its argument is provided, so the
        method can be used for status-only, pet-only, or combined filtering
        without separate helper methods.

        Args:
            tasks:     Tasks to filter. Defaults to all tasks for this owner.
            completed: If True, keep only completed tasks. If False, keep only
                       pending tasks. If None, completion status is not filtered.
            pet_name:  If provided, keep only tasks whose pet name matches
                       exactly (case-sensitive). If None, all pets are included.

        Returns:
            A new list containing only the tasks that match all supplied filters.
        """
        if tasks is None:
            tasks = self.owner.all_tasks()
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet and t.pet.name == pet_name]
        return tasks

    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Detect scheduling conflicts and return human-readable warning messages.

        Two tasks conflict when they share the same preferred_time slot — the
        owner cannot attend to two pets simultaneously regardless of which pets
        are involved.  Uses itertools.combinations to generate every unique pair
        within a slot without duplicates or index arithmetic.

        Tasks with no preferred_time are skipped because they have no declared
        slot to conflict with.  The method never raises an exception; callers
        receive an empty list when no conflicts exist.

        Args:
            tasks: Tasks to check. Defaults to all pending tasks for this owner.

        Returns:
            A list of warning strings, one per conflicting pair.  Empty when
            no conflicts are detected.
        """
        if tasks is None:
            tasks = self.owner.pending_tasks()

        # Group pending tasks by their time slot
        slot_buckets: Dict[str, List[Task]] = {}
        for task in tasks:
            slot = (task.preferred_time or "").lower()
            if not slot:
                continue
            slot_buckets.setdefault(slot, []).append(task)

        warnings: List[str] = []
        for slot, slot_tasks in slot_buckets.items():
            if len(slot_tasks) < 2:
                continue
            for task_a, task_b in combinations(slot_tasks, 2):
                    pet_a = task_a.pet.name if task_a.pet else "unknown pet"
                    pet_b = task_b.pet.name if task_b.pet else "unknown pet"
                    warnings.append(
                        f"WARNING: '{task_a.title}' ({pet_a}) and "
                        f"'{task_b.title}' ({pet_b}) are both scheduled in the "
                        f"{slot} slot — possible conflict."
                    )
        return warnings

    def explain_choice(self, task: Task) -> str:
        """Return a human-readable explanation for a scheduled task."""
        pet_name = task.pet.name if task.pet else "the pet"
        return (
            f"{task.title} is scheduled for {pet_name} because it is "
            f"{task.priority} priority and fits within today's available time."
        )
