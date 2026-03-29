classDiagram
    class Owner {
        - name: str
        - availability: dict
        - preferences: dict
        - pets: list<Pet>
        + add_pet(pet: Pet)
        + set_availability(...)
        + prefers_task_type(task_type)
        + summary()
    }

    class Pet {
        - name: str
        - species: str
        - age: int
        - care_requirements: list[str]
        - preferences: dict
        + needs_care()
        + preferred_activity_times()
        + describe()
    }

    class Task {
        - title: str
        - duration_minutes: int
        - priority: str
        - task_type: str
        - pet: Pet
        - preferred_time: str
        + is_high_priority()
        + fits_in_window(window)
        + describe_reason()
    }

    class Scheduler {
        - owner: Owner
        - pet: Pet
        - task_list: list<Task>
        - constraints: dict
        + generate_schedule()
        + rank_tasks()
        + filter_tasks_by_constraints()
        + select_tasks_for_day()
        + explain_choice()
    }

    Owner "1" -- "*" Pet : owns
    Pet "1" -- "*" Task : has
    Scheduler --> Owner
    Scheduler --> Pet
    Scheduler --> Task
    