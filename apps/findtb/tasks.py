from celery.task.schedules import crontab
from celery.decorators import periodic_task

from findtb.management.commands import starteqa


@periodic_task(run_every=crontab(minute=0, hour=2))
def start_eqa():
    """
    Try to start EQA every day at 2 oclock
    """
    cmd = starteqa.Command()
    cmd.handle(all=True)



