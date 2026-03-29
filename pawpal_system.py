from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    task_type: Optional[str] = None
    pet_name: Optional[str] = None
    preferred_time: Optional[str] = None

    def is_high_priority(self) -> bool:
        raise NotImplementedError

    def fits_in_window(self, window: Dict[str, str]) -> bool:
        raise NotImplementedError

    def describe_reason(self) -> str:
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    care_requirements: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)

    def needs_care(self) -> List[str]:
        raise NotImplementedError

    def preferred_activity_times(self) -> List[str]:
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    availability: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def set_availability(self, availability: Dict[str, str]) -> None:
        raise NotImplementedError

    def prefers_task_type(self, task_type: str) -> bool:
        raise NotImplementedError

    def summary(self) -> str:
        raise NotImplementedError


@dataclass
class Scheduler:
    owner: Owner
    task_list: List[Task] = field(default_factory=list)
    constraints: Dict[str, str] = field(default_factory=dict)

    def generate_schedule(self) -> List[Task]:
        raise NotImplementedError

    def rank_tasks(self) -> List[Task]:
        raise NotImplementedError

    def filter_tasks_by_constraints(self) -> List[Task]:
        raise NotImplementedError

    def select_tasks_for_day(self) -> List[Task]:
        raise NotImplementedError

    def explain_choice(self, task: Task) -> str:
        raise NotImplementedError
