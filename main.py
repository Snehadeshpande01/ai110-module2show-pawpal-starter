from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(tasks):
    print("Today's Schedule")
    print("================")
    for index, task in enumerate(tasks, start=1):
        pet_name = task.pet.name if task.pet else "Unknown pet"
        preferred = f" (preferred: {task.preferred_time})" if task.preferred_time else ""
        print(
            f"{index}. {task.title} for {pet_name} - {task.duration_minutes} min - "
            f"priority={task.priority}{preferred}"
        )


if __name__ == "__main__":
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=2)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    task1 = Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        task_type="walk",
        preferred_time="morning",
    )
    task2 = Task(
        title="Feed breakfast",
        duration_minutes=10,
        priority="medium",
        task_type="feed",
        preferred_time="morning",
    )
    task3 = Task(
        title="Evening play",
        duration_minutes=20,
        priority="low",
        task_type="play",
        preferred_time="evening",
    )

    mochi.add_task(task1)
    mochi.add_task(task2)
    luna.add_task(task3)

    scheduler = Scheduler(owner=owner, constraints={"max_daily_minutes": "120"})
    today_tasks = scheduler.generate_schedule()

    print_schedule(today_tasks)
