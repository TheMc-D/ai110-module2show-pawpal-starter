from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner

st.subheader("Owner & Pets")
owner.name = st.text_input("Owner name", value=owner.name)

with st.form("add_pet_form", clear_on_submit=True):
    st.markdown("**Add a pet**")
    pet_col1, pet_col2 = st.columns(2)
    with pet_col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with pet_col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species))

if owner.pets:
    st.write("Current pets:", ", ".join(pet.name for pet in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Scheduling preferences")
st.caption("Used to build today's schedule and to check tasks against your daily time budget.")

sched_col1, sched_col2 = st.columns(2)
with sched_col1:
    available_time_minutes = st.number_input(
        "Available time (minutes)", min_value=1, max_value=600, value=60
    )
with sched_col2:
    start_time = st.text_input("Start time (HH:MM)", value="08:00")

scheduler = Scheduler(available_time_minutes=int(available_time_minutes), start_time=start_time)

st.divider()

st.subheader("Tasks")
st.caption("Add care tasks to a pet. These feed directly into the scheduler below.")

if owner.pets:
    selected_pet_name = st.selectbox("Pet", [pet.name for pet in owner.pets])
    selected_pet = next(pet for pet in owner.pets if pet.name == selected_pet_name)

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            category = st.selectbox(
                "Category", ["walk", "feeding", "medication", "grooming", "enrichment", "other"]
            )
        with col3:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col4:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")
        if st.form_submit_button("Add task"):
            selected_pet.add_task(
                Task(
                    title=task_title,
                    category=category,
                    duration_minutes=int(duration),
                    priority=priority,
                    preferred_time=preferred_time or None,
                )
            )

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            pet_filter = st.selectbox("Filter by pet", ["All"] + [pet.name for pet in owner.pets])
        with filter_col2:
            status_filter = st.selectbox("Filter by status", ["All", "Completed", "Incomplete"])
        with filter_col3:
            sort_by_time = st.checkbox("Sort by preferred time")

        completed_filter = {"All": None, "Completed": True, "Incomplete": False}[status_filter]
        display_tasks = owner.filter_tasks(
            pet_name=None if pet_filter == "All" else pet_filter,
            completed=completed_filter,
        )
        if sort_by_time:
            display_tasks = scheduler.sort_by_time(display_tasks)

        st.write(f"Showing {len(display_tasks)} of {len(all_tasks)} tasks:")
        st.table(
            [
                {
                    "pet": task.pet.name if task.pet else "",
                    "title": task.title,
                    "category": task.category,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "preferred_time": task.preferred_time or "",
                    "completed": task.completed,
                }
                for task in display_tasks
            ]
        )

        if st.button("Check for time conflicts"):
            conflicts = scheduler.detect_conflicts(owner.get_tasks_due_today(date.today()))
            if conflicts:
                for warning in conflicts:
                    st.warning(warning)
            else:
                st.success("No time conflicts among today's tasks.")
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("Add a pet before adding tasks.")

st.divider()

st.subheader("Build Schedule")
st.caption("Builds today's plan from your pets' tasks, ordered by priority and fit to the time budget.")

if st.button("Generate schedule"):
    plan = scheduler.build_schedule(owner, date.today())
    st.text(plan.to_display())
    for scheduled in plan.scheduled_tasks:
        st.caption(scheduler.explain(scheduled.task))
