from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler


def test_pet_task_addition():
    pet = Pet(name="Buddy", species="dog", age=4)
    task = Task(title="Feed breakfast", duration_minutes=10, priority="medium")
    pet.add_task(task)

    assert task.pet is pet
    assert pet.tasks == [task]
    assert pet.pending_tasks() == [task]


def test_scheduler_respects_daily_limit():
    owner = Owner(name="Sam")
    pet = Pet(name="Luna", species="cat")
    owner.add_pet(pet)

    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high", task_type="walk"))
    pet.add_task(Task(title="Play", duration_minutes=20, priority="medium", task_type="play"))
    pet.add_task(Task(title="Brush", duration_minutes=20, priority="low", task_type="groom"))

    scheduler = Scheduler(owner=owner, constraints={"max_daily_minutes": "40"})
    schedule = scheduler.generate_schedule()

    assert [task.title for task in schedule] == ["Walk", "Play"]


def test_task_description_and_reason():
    task = Task(title="Feed breakfast", duration_minutes=10, priority="high", task_type="feed")
    assert "high priority" in task.describe_reason()


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """Tasks come back morning → afternoon → evening regardless of insertion order."""
    owner = Owner(name="Alex")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task(title="Evening walk", duration_minutes=30, preferred_time="evening"))
    pet.add_task(Task(title="Afternoon play", duration_minutes=20, preferred_time="afternoon"))
    pet.add_task(Task(title="Morning feed", duration_minutes=10, preferred_time="morning"))

    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_time()

    assert [t.title for t in sorted_tasks] == [
        "Morning feed",
        "Afternoon play",
        "Evening walk",
    ]


def test_sort_by_time_no_preferred_time_goes_last():
    """A task with no preferred_time falls to the end of the sorted list."""
    owner = Owner(name="Alex")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task(title="Anytime task", duration_minutes=15))  # no preferred_time
    pet.add_task(Task(title="Morning feed", duration_minutes=10, preferred_time="morning"))

    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_time()

    assert sorted_tasks[0].title == "Morning feed"
    assert sorted_tasks[-1].title == "Anytime task"


def test_sort_by_time_all_same_slot_preserves_relative_order():
    """Tasks sharing the same slot keep a stable relative order."""
    owner = Owner(name="Alex")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task(title="First morning", duration_minutes=10, preferred_time="morning"))
    pet.add_task(Task(title="Second morning", duration_minutes=10, preferred_time="morning"))

    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_time()

    # Both are in the morning slot; stable sort keeps insertion order.
    assert [t.title for t in sorted_tasks] == ["First morning", "Second morning"]


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_recurring_task_spawns_next_day():
    """Completing a daily task adds a new task due the following day."""
    pet = Pet(name="Buddy", species="dog")
    today = date(2024, 6, 1)
    task = Task(
        title="Morning walk",
        duration_minutes=20,
        frequency="daily",
        due_date=today,
    )
    pet.add_task(task)

    task.mark_completed()

    assert task.completed is True
    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task.title == "Morning walk"
    assert next_task.due_date == date(2024, 6, 2)
    assert next_task.completed is False


def test_weekly_recurring_task_spawns_seven_days_later():
    """Completing a weekly task adds a new task due seven days later."""
    pet = Pet(name="Luna", species="cat")
    today = date(2024, 6, 1)
    task = Task(
        title="Grooming",
        duration_minutes=30,
        frequency="weekly",
        due_date=today,
    )
    pet.add_task(task)

    task.mark_completed()

    next_task = pet.tasks[1]
    assert next_task.due_date == date(2024, 6, 8)


def test_recurring_task_without_due_date_uses_today():
    """When due_date is None, the next occurrence is calculated from today."""
    pet = Pet(name="Max", species="dog")
    task = Task(title="Feed", duration_minutes=10, frequency="daily")
    pet.add_task(task)

    task.mark_completed()

    expected_next = date.today() + timedelta(days=1)
    assert pet.tasks[1].due_date == expected_next


def test_unknown_frequency_does_not_spawn_next_task():
    """An unrecognised frequency (e.g. 'monthly') must not create a new task."""
    pet = Pet(name="Milo", species="cat")
    task = Task(title="Vet visit", duration_minutes=60, frequency="monthly")
    pet.add_task(task)

    task.mark_completed()

    assert len(pet.tasks) == 1  # no new task spawned


def test_non_recurring_task_does_not_spawn_next_task():
    """A task with no frequency must not create a follow-up task on completion."""
    pet = Pet(name="Bella", species="dog")
    task = Task(title="Bath", duration_minutes=45)
    pet.add_task(task)

    task.mark_completed()

    assert len(pet.tasks) == 1


def test_recurring_task_without_pet_does_not_crash():
    """mark_completed on an orphan recurring task should not raise."""
    task = Task(title="Feed", duration_minutes=10, frequency="daily", due_date=date(2024, 6, 1))
    task.mark_completed()  # pet is None — should return early without error
    assert task.completed is True


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_conflict_detected_for_same_time_slot():
    """Two tasks in the same slot produce exactly one conflict warning."""
    owner = Owner(name="Jordan")
    pet_a = Pet(name="Ace", species="dog")
    pet_b = Pet(name="Zara", species="cat")
    owner.add_pet(pet_a)
    owner.add_pet(pet_b)

    pet_a.add_task(Task(title="Walk Ace", duration_minutes=20, preferred_time="morning"))
    pet_b.add_task(Task(title="Feed Zara", duration_minutes=10, preferred_time="morning"))

    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Walk Ace" in warnings[0]
    assert "Feed Zara" in warnings[0]
    assert "morning" in warnings[0]


def test_no_conflict_for_different_time_slots():
    """Tasks in different slots must not produce any warnings."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Ace", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task(title="Morning feed", duration_minutes=10, preferred_time="morning"))
    pet.add_task(Task(title="Evening walk", duration_minutes=30, preferred_time="evening"))

    scheduler = Scheduler(owner=owner)
    assert scheduler.detect_conflicts() == []


def test_three_tasks_same_slot_yields_three_warnings():
    """Three tasks in one slot produce one warning per unique pair (3 pairs)."""
    owner = Owner(name="Casey")
    for name in ("Ace", "Boo", "Cleo"):
        pet = Pet(name=name, species="dog")
        owner.add_pet(pet)
        pet.add_task(Task(title=f"Walk {name}", duration_minutes=20, preferred_time="afternoon"))

    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 3


def test_completed_tasks_excluded_from_conflict_detection():
    """Completed tasks must not be counted when checking for conflicts."""
    owner = Owner(name="Pat")
    pet = Pet(name="Duke", species="dog")
    owner.add_pet(pet)

    done = Task(title="Morning walk", duration_minutes=20, preferred_time="morning", completed=True)
    pending = Task(title="Morning feed", duration_minutes=10, preferred_time="morning")
    pet.add_task(done)
    pet.add_task(pending)

    scheduler = Scheduler(owner=owner)
    # Only one pending task in the morning slot — no conflict.
    assert scheduler.detect_conflicts() == []


def test_task_without_preferred_time_not_flagged_as_conflict():
    """Tasks with no preferred_time should be skipped by conflict detection."""
    owner = Owner(name="Sam")
    pet = Pet(name="Pip", species="cat")
    owner.add_pet(pet)

    pet.add_task(Task(title="Task A", duration_minutes=10))
    pet.add_task(Task(title="Task B", duration_minutes=10))

    scheduler = Scheduler(owner=owner)
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Edge cases: empty / boundary states
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_returns_empty_schedule():
    """A pet with no tasks must not cause errors; schedule should be empty."""
    owner = Owner(name="Chris")
    owner.add_pet(Pet(name="Ghost", species="cat"))

    scheduler = Scheduler(owner=owner)
    assert scheduler.generate_schedule() == []


def test_owner_with_no_pets_returns_empty_schedule():
    """An owner with no pets registered should produce an empty schedule."""
    scheduler = Scheduler(owner=Owner(name="Loner"))
    assert scheduler.generate_schedule() == []


def test_daily_limit_exactly_met_includes_task():
    """A task whose duration exactly fills the remaining budget must be included."""
    owner = Owner(name="Dana")
    pet = Pet(name="Bolt", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task(title="Exact fit", duration_minutes=30, priority="medium"))

    scheduler = Scheduler(owner=owner, constraints={"max_daily_minutes": "30"})
    schedule = scheduler.generate_schedule()

    assert len(schedule) == 1
    assert schedule[0].title == "Exact fit"


def test_task_exceeding_daily_limit_is_excluded():
    """A single task that exceeds the daily budget must not appear in the schedule."""
    owner = Owner(name="Dana")
    pet = Pet(name="Bolt", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task(title="Too long", duration_minutes=60, priority="high"))

    scheduler = Scheduler(owner=owner, constraints={"max_daily_minutes": "30"})
    assert scheduler.generate_schedule() == []
