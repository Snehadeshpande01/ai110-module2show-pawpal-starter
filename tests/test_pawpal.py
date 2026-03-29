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
