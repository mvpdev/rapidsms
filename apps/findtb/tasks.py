from celery.task.schedules import crontab
from celery.decorators import periodic_task
from findtb.management.commands import starteqa

# Try to start EQA every day at 2 oclock
@periodic_task(run_every=crontab(minute=0, hour=2))
def start_eqa():
    cmd = starteqa.Command()
    cmd.handle(all=True)

