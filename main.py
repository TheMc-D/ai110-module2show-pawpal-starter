from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler

owner = Owner(name="Jordan")

dog = Pet(name="Mochi", species="dog", breed="Shiba Inu")
cat = Pet(name="Biscuit", species="cat", breed="Tabby")
owner.add_pet(dog)
owner.add_pet(cat)

dog.add_task(Task(title="Morning walk", category="walk", duration_minutes=30, priority="high", preferred_time="08:00"))
dog.add_task(Task(title="Feeding", category="feeding", duration_minutes=10, priority="high", preferred_time="08:30"))
cat.add_task(Task(title="Litter box cleaning", category="grooming", duration_minutes=15, priority="medium", preferred_time="09:00"))
cat.add_task(Task(title="Playtime", category="enrichment", duration_minutes=45, priority="low", preferred_time="09:30"))

scheduler = Scheduler(available_time_minutes=60, start_time="08:00")
plan = scheduler.build_schedule(owner, date.today())

print("Today's Schedule")
print(plan.to_display())
