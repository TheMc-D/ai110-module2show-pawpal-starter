from datetime import date

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def make_task(**overrides):
    defaults = dict(title="Task", category="walk", duration_minutes=10, priority="medium")
    defaults.update(overrides)
    return Task(**defaults)


def test_mark_complete_changes_task_status():
    task = Task(title="Feeding", category="feeding", duration_minutes=10, priority="high")

    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Morning walk", category="walk", duration_minutes=30, priority="high")

    assert len(pet.tasks) == 0
    pet.add_task(task)
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

class TestSortingCorrectness:
    def test_sort_by_priority_orders_high_before_medium_before_low(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="Low", priority="low"),
            make_task(title="High", priority="high"),
            make_task(title="Medium", priority="medium"),
        ]

        ordered = scheduler.sort_by_priority(tasks)

        assert [task.title for task in ordered] == ["High", "Medium", "Low"]

    def test_sort_by_priority_ties_broken_by_shorter_duration(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="Long", priority="high", duration_minutes=30),
            make_task(title="Short", priority="high", duration_minutes=5),
        ]

        ordered = scheduler.sort_by_priority(tasks)

        assert [task.title for task in ordered] == ["Short", "Long"]

    def test_sort_by_time_orders_tasks_chronologically(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="Evening", preferred_time="18:00"),
            make_task(title="Morning", preferred_time="08:00"),
            make_task(title="Midday", preferred_time="12:00"),
        ]

        ordered = scheduler.sort_by_time(tasks)

        assert [task.title for task in ordered] == ["Morning", "Midday", "Evening"]

    def test_sort_by_time_tasks_without_preferred_time_sort_last(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="No time"),
            make_task(title="Has time", preferred_time="09:00"),
        ]

        ordered = scheduler.sort_by_time(tasks)

        assert [task.title for task in ordered] == ["Has time", "No time"]


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

class TestRecurrenceLogic:
    def test_daily_task_completion_creates_task_for_next_day(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(title="Feeding", recurrence="daily")
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))

        assert task.completed is True
        assert len(pet.tasks) == 2
        next_task = pet.tasks[1]
        assert next_task.title == "Feeding"
        assert next_task.completed is False
        assert next_task.due_date == date(2026, 7, 7)

    def test_weekly_task_completion_creates_task_for_next_matching_weekday(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(title="Grooming", recurrence="weekly", days_of_week=[0, 2, 4])  # Mon/Wed/Fri
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))  # a Monday

        next_task = pet.tasks[1]
        assert next_task.completed is False
        assert next_task.due_date == date(2026, 7, 8)  # the following Wednesday

    def test_weekly_task_with_no_day_pattern_recurs_seven_days_later(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(title="Nail trim", recurrence="weekly")
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))

        next_task = pet.tasks[1]
        assert next_task.due_date == date(2026, 7, 13)

    def test_one_time_task_completion_does_not_create_a_new_task(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(title="Vet visit", recurrence="one-time")
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))

        assert len(pet.tasks) == 1

    def test_completed_task_no_longer_shows_as_due_today(self):
        task = make_task(recurrence="one-time")

        assert task.is_due_today(date(2026, 7, 6)) is True
        task.mark_complete(date(2026, 7, 6))
        assert task.is_due_today(date(2026, 7, 6)) is False


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def test_two_tasks_at_the_exact_same_time_are_flagged_as_a_conflict(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="Walk", duration_minutes=15, preferred_time="08:00"),
            make_task(title="Feeding", duration_minutes=10, preferred_time="08:00"),
        ]

        warnings = scheduler.detect_conflicts(tasks)

        assert len(warnings) == 1
        assert "Walk" in warnings[0] and "Feeding" in warnings[0]

    def test_partially_overlapping_tasks_produce_a_warning(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="Vet checkup", duration_minutes=20, preferred_time="08:00"),
            make_task(title="Grooming", duration_minutes=15, preferred_time="08:10"),
        ]

        warnings = scheduler.detect_conflicts(tasks)

        assert len(warnings) == 1
        assert "Vet checkup" in warnings[0] and "Grooming" in warnings[0]

    def test_back_to_back_tasks_do_not_conflict(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="First", duration_minutes=20, preferred_time="08:00"),
            make_task(title="Second", duration_minutes=15, preferred_time="08:20"),
        ]

        assert scheduler.detect_conflicts(tasks) == []

    def test_tasks_without_a_preferred_time_are_never_flagged(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [make_task(title="Untimed A"), make_task(title="Untimed B")]

        assert scheduler.detect_conflicts(tasks) == []

    def test_conflicts_are_detected_across_different_pets(self):
        owner = Owner(name="Jordan")
        dog = Pet(name="Mochi", species="dog")
        cat = Pet(name="Biscuit", species="cat")
        owner.add_pet(dog)
        owner.add_pet(cat)
        dog.add_task(make_task(title="Dog walk", duration_minutes=30, preferred_time="09:00"))
        cat.add_task(make_task(title="Cat vet visit", duration_minutes=20, preferred_time="09:15"))

        warnings = Scheduler(available_time_minutes=60, start_time="08:00").detect_conflicts(
            owner.get_all_tasks()
        )

        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_pet_with_no_tasks_has_nothing_due_today(self):
        pet = Pet(name="Mochi", species="dog")

        assert pet.get_tasks_due_today(date(2026, 7, 6)) == []

    def test_owner_with_no_pets_has_no_tasks_due_today(self):
        owner = Owner(name="Jordan")

        assert owner.get_tasks_due_today(date(2026, 7, 6)) == []

    def test_schedule_with_no_due_tasks_produces_an_empty_plan(self):
        owner = Owner(name="Jordan")
        pet = Pet(name="Mochi", species="dog")
        owner.add_pet(pet)
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")

        plan = scheduler.build_schedule(owner, date(2026, 7, 6))

        assert plan.scheduled_tasks == []
        assert plan.dropped_tasks == []
        assert plan.conflict_warnings == []

    def test_zero_duration_task_is_rejected_at_creation(self):
        with pytest.raises(ValueError):
            make_task(title="Quick check", duration_minutes=0)

    def test_negative_duration_task_is_rejected_at_creation(self):
        with pytest.raises(ValueError):
            make_task(title="Invalid", duration_minutes=-5)
