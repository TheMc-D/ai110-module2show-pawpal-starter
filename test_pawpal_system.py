from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def make_task(**overrides):
    defaults = dict(title="Task", category="walk", duration_minutes=10, priority="medium")
    defaults.update(overrides)
    return Task(**defaults)


class TestIsDueToday:
    def test_one_time_task_is_due_until_completed(self):
        task = make_task(recurrence="one-time")
        assert task.is_due_today(date(2026, 7, 6)) is True
        task.mark_complete()
        assert task.is_due_today(date(2026, 7, 6)) is False

    def test_daily_task_is_due_every_day_until_completed(self):
        task = make_task(recurrence="daily")
        assert task.is_due_today(date(2026, 7, 6)) is True
        assert task.is_due_today(date(2026, 7, 7)) is True

    def test_weekly_task_only_due_on_matching_weekday(self):
        task = make_task(recurrence="weekly", days_of_week=[0, 2, 4])  # Mon/Wed/Fri
        assert task.is_due_today(date(2026, 7, 6)) is True   # Monday
        assert task.is_due_today(date(2026, 7, 7)) is False  # Tuesday

    def test_due_date_overrides_days_of_week_once_set(self):
        task = make_task(recurrence="weekly", days_of_week=[0, 2, 4], due_date=date(2026, 7, 8))
        assert task.is_due_today(date(2026, 7, 6)) is False  # Monday, but due_date says Wednesday
        assert task.is_due_today(date(2026, 7, 8)) is True


class TestRecurringAutomation:
    def test_daily_completion_spawns_next_day(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(recurrence="daily")
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))

        assert task.completed is True
        assert len(pet.tasks) == 2
        next_task = pet.tasks[1]
        assert next_task.completed is False
        assert next_task.due_date == date(2026, 7, 7)

    def test_weekly_single_day_completion_spawns_seven_days_later(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(recurrence="weekly", days_of_week=[5])  # Saturday only
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 4))  # a Saturday

        next_task = pet.tasks[1]
        assert next_task.due_date == date(2026, 7, 11)

    def test_weekly_multi_day_completion_spawns_next_matching_weekday(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(recurrence="weekly", days_of_week=[0, 2, 4])  # Mon/Wed/Fri
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))  # Monday

        next_task = pet.tasks[1]
        assert next_task.due_date == date(2026, 7, 8)  # Wednesday, not next Monday

    def test_one_time_completion_spawns_nothing(self):
        pet = Pet(name="Mochi", species="dog")
        task = make_task(recurrence="one-time")
        pet.add_task(task)

        task.mark_complete(date(2026, 7, 6))

        assert len(pet.tasks) == 1


class TestFilterTasks:
    def _build_owner(self):
        owner = Owner(name="Jordan")
        dog = Pet(name="Mochi", species="dog")
        cat = Pet(name="Biscuit", species="cat")
        owner.add_pet(dog)
        owner.add_pet(cat)
        dog.add_task(make_task(title="Walk", completed=False))
        dog.add_task(make_task(title="Feeding", completed=True))
        cat.add_task(make_task(title="Playtime", completed=False))
        return owner

    def test_filter_by_pet_name(self):
        owner = self._build_owner()
        titles = {task.title for task in owner.filter_tasks(pet_name="Mochi")}
        assert titles == {"Walk", "Feeding"}

    def test_filter_by_completed(self):
        owner = self._build_owner()
        titles = {task.title for task in owner.filter_tasks(completed=True)}
        assert titles == {"Feeding"}

    def test_filter_by_pet_and_completed(self):
        owner = self._build_owner()
        titles = {task.title for task in owner.filter_tasks(pet_name="Mochi", completed=False)}
        assert titles == {"Walk"}

    def test_no_filters_returns_everything(self):
        owner = self._build_owner()
        assert len(owner.filter_tasks()) == 3


class TestSortByTime:
    def test_sorts_ascending_by_preferred_time(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="Evening", preferred_time="18:00"),
            make_task(title="Morning", preferred_time="08:00"),
            make_task(title="Midday", preferred_time="12:00"),
        ]
        ordered = scheduler.sort_by_time(tasks)
        assert [task.title for task in ordered] == ["Morning", "Midday", "Evening"]

    def test_tasks_without_preferred_time_sort_last(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [
            make_task(title="No time"),
            make_task(title="Has time", preferred_time="09:00"),
        ]
        ordered = scheduler.sort_by_time(tasks)
        assert [task.title for task in ordered] == ["Has time", "No time"]


class TestDetectConflicts:
    def test_overlapping_tasks_produce_a_warning(self):
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

    def test_tasks_without_preferred_time_are_ignored(self):
        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        tasks = [make_task(title="Untimed A"), make_task(title="Untimed B")]
        assert scheduler.detect_conflicts(tasks) == []


class TestFilterByTime:
    def test_never_drops_a_higher_priority_task_for_a_lower_one(self):
        scheduler = Scheduler(available_time_minutes=30, start_time="08:00")
        tasks = scheduler.sort_by_priority([
            make_task(title="Important", duration_minutes=25, priority="high"),
            make_task(title="Small A", duration_minutes=15, priority="medium"),
            make_task(title="Small B", duration_minutes=15, priority="medium"),
        ])
        selected, dropped = scheduler.filter_by_time(tasks, 30)
        assert [task.title for task in selected] == ["Important"]
        assert {task.title for task in dropped} == {"Small A", "Small B"}

    def test_best_fits_within_a_tier_to_minimize_wasted_time(self):
        scheduler = Scheduler(available_time_minutes=10, start_time="08:00")
        tasks = scheduler.sort_by_priority([
            make_task(title="Five", duration_minutes=5, priority="medium"),
            make_task(title="Six", duration_minutes=6, priority="medium"),
        ])
        selected, dropped = scheduler.filter_by_time(tasks, 10)
        assert [task.title for task in selected] == ["Six"]
        assert [task.title for task in dropped] == ["Five"]


class TestBuildSchedule:
    def test_builds_a_plan_and_reports_conflicts(self):
        owner = Owner(name="Jordan")
        dog = Pet(name="Mochi", species="dog")
        owner.add_pet(dog)
        dog.add_task(make_task(title="Walk", duration_minutes=20, priority="high", preferred_time="08:00"))
        dog.add_task(make_task(title="Vet call", duration_minutes=15, priority="high", preferred_time="08:10"))

        scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
        plan = scheduler.build_schedule(owner, date(2026, 7, 6))

        assert len(plan.scheduled_tasks) == 2
        assert len(plan.conflict_warnings) == 1
        assert plan.total_time_used() == 35
