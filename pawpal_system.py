from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
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
    pet: Optional[Pet] = None
    preferred_time: Optional[str] = None
    frequency: Optional[str] = None
    completed: bool = False
    notes: Optional[str] = None

    def mark_completed(self) -> None:
        """Mark this task as completed."""
        self.completed = True

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

        preferred = self.preferred_time.lower()
        if preferred in {"morning", "am", "a.m."}:
            return start_window <= time(12, 0) and end_window >= time(8, 0)
        if preferred in {"afternoon", "pm", "p.m."}:
            return start_window <= time(18, 0) and end_window >= time(12, 0)
        if preferred in {"evening", "night"}:
            return start_window <= time(22, 0) and end_window >= time(17, 0)

        return True

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
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks across every pet."""
        return [task for task in self.all_tasks() if not task.completed]


@dataclass
class Scheduler:
    owner: Owner
    constraints: Dict[str, str] = field(default_factory=dict)

    def generate_schedule(self) -> List[Task]:
        """Generate a daily schedule from the owner's pending tasks."""
        tasks = [task for task in self.owner.pending_tasks()]
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

    def explain_choice(self, task: Task) -> str:
        """Return a human-readable explanation for a scheduled task."""
        pet_name = task.pet.name if task.pet else "the pet"
        return (
            f"{task.title} is scheduled for {pet_name} because it is "
            f"{task.priority} priority and fits within today's available time."
        )
