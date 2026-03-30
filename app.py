import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — powered by priority, time slots, and conflict detection.")

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
if "pets" not in st.session_state:
    st.session_state.pets: list[Pet] = []


def _get_owner() -> Owner:
    return st.session_state.owner


def _get_pets() -> list[Pet]:
    return st.session_state.pets


def _find_pet(name: str) -> Pet | None:
    return next((p for p in _get_pets() if p.name == name), None)


# ---------------------------------------------------------------------------
# Sidebar — owner & pet setup
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Owner & Pets")

    owner_name = st.text_input("Owner name", value=_get_owner().name)
    if owner_name != _get_owner().name:
        _get_owner().name = owner_name

    st.divider()
    st.subheader("Add a pet")
    new_pet_name = st.text_input("Pet name", placeholder="e.g. Mochi")
    new_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

    if st.button("Add pet", use_container_width=True):
        if not new_pet_name.strip():
            st.warning("Enter a pet name first.")
        elif _find_pet(new_pet_name.strip()):
            st.warning(f"{new_pet_name} is already registered.")
        else:
            pet = Pet(name=new_pet_name.strip(), species=new_species, age=int(new_age))
            _get_owner().add_pet(pet)
            _get_pets().append(pet)
            st.success(f"{new_pet_name} added!")

    if _get_pets():
        st.divider()
        st.subheader("Registered pets")
        for p in _get_pets():
            st.markdown(f"**{p.name}** — {p.species}, age {p.age}")

# ---------------------------------------------------------------------------
# Require at least one pet before showing the rest
# ---------------------------------------------------------------------------
if not _get_pets():
    st.info("Add at least one pet in the sidebar to get started.")
    st.stop()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_tasks, tab_schedule, tab_conflicts, tab_filter = st.tabs(
    ["Add Tasks", "Schedule", "Conflicts", "Filter & Search"]
)

# ============================================================
# TAB 1 — Add Tasks
# ============================================================
with tab_tasks:
    st.subheader("Add a task")

    col1, col2 = st.columns(2)
    with col1:
        selected_pet_name = st.selectbox("Pet", [p.name for p in _get_pets()], key="task_pet")
        task_title = st.text_input("Task title", value="Morning walk", key="task_title")
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20, key="task_dur"
        )
        priority = st.selectbox("Priority", ["high", "medium", "low"], key="task_pri")

    with col2:
        time_slot = st.selectbox(
            "Preferred time slot",
            ["(none)", "morning", "afternoon", "evening"],
            key="task_slot",
        )
        task_type = st.selectbox(
            "Task type",
            ["(none)", "feed", "walk", "play", "groom", "vet", "other"],
            key="task_type",
        )
        frequency = st.selectbox(
            "Recurring?",
            ["(none)", "daily", "weekly"],
            key="task_freq",
        )
        due_date_input = st.date_input("Due date", value=date.today(), key="task_due")

    if st.button("Add task", use_container_width=True):
        pet = _find_pet(selected_pet_name)
        task = Task(
            title=task_title.strip(),
            duration_minutes=int(duration),
            priority=priority,
            task_type=None if task_type == "(none)" else task_type,
            preferred_time=None if time_slot == "(none)" else time_slot,
            frequency=None if frequency == "(none)" else frequency,
            due_date=due_date_input,
        )
        pet.add_task(task)
        st.success(f"Added **{task_title}** for {selected_pet_name}.")

    # Show all tasks sorted by time slot
    owner = _get_owner()
    all_tasks = owner.all_tasks()
    if all_tasks:
        st.divider()
        scheduler = Scheduler(owner=owner)
        sorted_tasks = scheduler.sort_by_time(all_tasks)

        st.subheader("All tasks — sorted by time slot")
        rows = []
        for t in sorted_tasks:
            rows.append(
                {
                    "Pet": t.pet.name if t.pet else "—",
                    "Task": t.title,
                    "Priority": t.priority,
                    "Time slot": t.preferred_time or "(any time)",
                    "Duration (min)": t.duration_minutes,
                    "Recurring": t.frequency or "—",
                    "Due": str(t.due_date) if t.due_date else "—",
                    "Done": "✅" if t.completed else "⬜",
                }
            )
        st.table(rows)

        # Mark-complete controls
        st.subheader("Mark a task complete")
        pending = [t for t in all_tasks if not t.completed]
        if pending:
            task_to_complete = st.selectbox(
                "Select task",
                pending,
                format_func=lambda t: f"{t.pet.name if t.pet else '?'} — {t.title}",
                key="complete_sel",
            )
            if st.button("Mark complete"):
                task_to_complete.mark_completed()
                if task_to_complete.frequency:
                    st.success(
                        f"**{task_to_complete.title}** marked done. "
                        f"Next {task_to_complete.frequency} occurrence added automatically."
                    )
                else:
                    st.success(f"**{task_to_complete.title}** marked done.")
        else:
            st.success("All tasks are complete!")
    else:
        st.info("No tasks yet — add one above.")

# ============================================================
# TAB 2 — Schedule
# ============================================================
with tab_schedule:
    st.subheader("Generate today's schedule")

    max_minutes = st.slider(
        "Daily time budget (minutes)", min_value=10, max_value=480, value=120, step=10
    )

    if st.button("Generate schedule", use_container_width=True):
        scheduler = Scheduler(
            owner=_get_owner(), constraints={"max_daily_minutes": str(max_minutes)}
        )
        schedule = scheduler.generate_schedule()

        if not schedule:
            st.warning("No tasks could be scheduled. Add tasks or increase the time budget.")
        else:
            total = sum(t.duration_minutes for t in schedule)
            st.success(
                f"Schedule ready — **{len(schedule)} task(s)**, "
                f"**{total} of {max_minutes} minutes** used."
            )

            rows = []
            for t in schedule:
                rows.append(
                    {
                        "Pet": t.pet.name if t.pet else "—",
                        "Task": t.title,
                        "Priority": t.priority,
                        "Time slot": t.preferred_time or "(any time)",
                        "Duration (min)": t.duration_minutes,
                        "Why scheduled": scheduler.explain_choice(t),
                    }
                )
            st.table(rows)

            # Skipped tasks
            ranked = scheduler.rank_tasks()
            skipped = [t for t in ranked if t not in schedule and not t.completed]
            if skipped:
                with st.expander(f"⚠️ {len(skipped)} task(s) skipped (over budget)"):
                    for t in skipped:
                        st.markdown(
                            f"- **{t.title}** ({t.pet.name if t.pet else '?'}) "
                            f"— {t.duration_minutes} min, {t.priority} priority"
                        )

# ============================================================
# TAB 3 — Conflict Detection
# ============================================================
with tab_conflicts:
    st.subheader("Conflict detection")
    st.caption(
        "Two tasks conflict when they share the same time slot — "
        "you can't attend to two pets simultaneously."
    )

    if st.button("Check for conflicts", use_container_width=True):
        scheduler = Scheduler(owner=_get_owner())
        warnings = scheduler.detect_conflicts()

        if not warnings:
            st.success("No conflicts found — your schedule looks clear!")
        else:
            st.error(f"{len(warnings)} conflict(s) detected:")
            for w in warnings:
                st.warning(w)

            st.caption(
                "Tip: resolve conflicts by changing the preferred time slot "
                "of one of the tasks above."
            )

# ============================================================
# TAB 4 — Filter & Search
# ============================================================
with tab_filter:
    st.subheader("Filter tasks")

    col_a, col_b = st.columns(2)
    with col_a:
        filter_pet = st.selectbox(
            "Filter by pet",
            ["(all pets)"] + [p.name for p in _get_pets()],
            key="filter_pet",
        )
    with col_b:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Pending only", "Completed only"],
            key="filter_status",
        )

    scheduler = Scheduler(owner=_get_owner())

    completed_arg = None
    if filter_status == "Pending only":
        completed_arg = False
    elif filter_status == "Completed only":
        completed_arg = True

    pet_name_arg = None if filter_pet == "(all pets)" else filter_pet

    results = scheduler.filter_tasks(completed=completed_arg, pet_name=pet_name_arg)

    if results:
        st.markdown(f"**{len(results)} task(s) matched.**")
        rows = []
        for t in results:
            rows.append(
                {
                    "Pet": t.pet.name if t.pet else "—",
                    "Task": t.title,
                    "Priority": t.priority,
                    "Time slot": t.preferred_time or "(any time)",
                    "Duration (min)": t.duration_minutes,
                    "Status": "✅ Done" if t.completed else "⬜ Pending",
                }
            )
        st.table(rows)
    else:
        st.info("No tasks match the selected filters.")
