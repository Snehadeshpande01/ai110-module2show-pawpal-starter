from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(tasks):
    print("================")
    for index, task in enumerate(tasks, start=1):
        pet_name = task.pet.name if task.pet else "Unknown pet"
        preferred = f" (preferred: {task.preferred_time})" if task.preferred_time else ""
        status = " [done]" if task.completed else ""
        due = f" due={task.due_date}" if task.due_date else ""
        freq = f" [{task.frequency}]" if task.frequency else ""
        print(
            f"{index}. {task.title} for {pet_name} - {task.duration_minutes} min - "
            f"priority={task.priority}{preferred}{freq}{due}{status}"
        )
    if not tasks:
        print("  (no tasks)")
    print()


if __name__ == "__main__":
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=2)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    # Tasks added OUT OF ORDER (evening first, then morning tasks)
    task1 = Task(
        title="Evening play",
        duration_minutes=20,
        priority="low",
        task_type="play",
        preferred_time="evening",
        frequency="weekly",
        due_date=today,
    )
    task2 = Task(
        title="Afternoon groom",
        duration_minutes=15,
        priority="medium",
        task_type="groom",
        preferred_time="afternoon",
    )
    task3 = Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        task_type="walk",
        preferred_time="morning",
        frequency="daily",
        due_date=today,
    )
    task4 = Task(
        title="Feed breakfast",
        duration_minutes=10,
        priority="medium",
        task_type="feed",
        preferred_time="morning",
    )

    # Deliberate conflict: two tasks in the same "morning" slot for different pets
    task5 = Task(
        title="Morning brush",
        duration_minutes=10,
        priority="medium",
        task_type="groom",
        preferred_time="morning",   # same slot as task3 and task4
    )
    luna.add_task(task5)            # Luna — different pet, same time slot

    luna.add_task(task1)    # evening
    mochi.add_task(task2)   # afternoon
    mochi.add_task(task3)   # morning
    mochi.add_task(task4)   # morning

    scheduler = Scheduler(owner=owner, constraints={"max_daily_minutes": "120"})

    print("--- Sorted by time (morning > afternoon > evening) ---")
    print_schedule(scheduler.sort_by_time())

    print("--- Mochi's tasks only ---")
    print_schedule(scheduler.filter_tasks(pet_name="Mochi"))

    # Conflict detection — runs before any tasks are completed
    print("--- Conflict detection ---")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(warning)
    else:
        print("No conflicts detected.")
    print()

    # Demo recurring tasks: mark daily and weekly tasks complete
    from datetime import timedelta
    print(f"--- Marking recurring tasks complete (today = {today}) ---")
    task3.mark_completed()  # daily: Morning walk -> new task due tomorrow
    task1.mark_completed()  # weekly: Evening play -> new task due in 7 days
    print(f"  'Morning walk' (daily) marked done. Next due: {today + timedelta(days=1)}")
    print(f"  'Evening play' (weekly) marked done. Next due: {today + timedelta(weeks=1)}")
    print()

    print("--- Pending (incomplete) tasks only — includes auto-created recurrences ---")
    print_schedule(scheduler.filter_tasks(completed=False))

    print("--- Completed tasks only ---")
    print_schedule(scheduler.filter_tasks(completed=True))

    print("--- Today's generated schedule ---")
    print_schedule(scheduler.generate_schedule())
