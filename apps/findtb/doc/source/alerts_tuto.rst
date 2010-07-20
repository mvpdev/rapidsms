*****************************************
How to set up alerts
*****************************************

Tasks Basics
===============

Put all your code in *tasks.py*, as it autodiscover tasks. If you don't,
you will have to register manually your tasks. 

If you modify *tasks.py*, you need to restart *celeryd*.

Hello world::

    from celery.decorators import task

    # set a fonction with the task decorator
    @task()
    def hello(name):
        return "Hello", name
        
    # DO NOT DO:
    hello("World") # runs immidiatly, without celery  
       
    # DO: 
    task_status = hello.delay("World") # this does not give you the result but a status
    # dispite the name, there is no delay, this line runs IMMIDIATLY after the line above

    # returns True if the task has finished processing.
    task_status.ready() 

    # is None as long as the tasks is not done
    # then contain the result (if any) or the exception (if the tasks raised one)
    task_status.result # task is not ready, so no return value yet.

    # This waits until the task is done and returns the result.
    result.get()  
    # This line won't be executed a long as the task is not done. Even if the 
    # task is scheduled in 10 years

    # returns True if the task didn't end in failure.
    result.successful() 
    
    
How to apply to alerts ?    
===============================

.. note:: Scheduled alerts are persistent between *celeryd* restarts.

Alerts in the future
---------------------------

You want to send an alert if somebody is late on some task:: 
   
    @task()
    def two_days_late(reporter):
        if reporter.is_late():
            send_msg(reporter, "You are late, you lazy!")
        
    # Use a standard timedelta to choose a delay    
    two_days = datetime.timedelta(seconds=3600 * 48)   
    today = datetime.datetime.today()     
    two_days_late.apply_async(eta=today + two_days,
                              args=(reporter,))
    
    # you need to restart celeryd, as usual
    
For fancy durations, use dateutil::

    >>> import datetime
    >>> from dateutil import relativedelta
    >>> now = datetime.datetime.today() 
    >>> delta = relativedelta.relativedelta(months=+1, weeks=-1, hour=10)
    >>> later = now + delta
    >>> later.month, later.day, later.hour
    (8, 13, 10)

``relativedelta`` is compatible with with the timedelta API.


Recurring alerts
--------------------------

This needs *celerybeat* to be running. Use ``-B`` option when running *celeryd*.

Crontab like::

    from celery.decorators import periodic_task
    from datetime import timedelta

    # just use timedelta as an interval
    # no need to call it, just restart celeryd
    d = timedelta(seconds=1)
    @periodic_task(run_every=d)
    def clock(name="ticker"):
        print("Tic") # send an SMS
        
    # Want to know what's going on ? 
    # use the task_id to get your task back (task_id is automatically calculated or equal to "name" if given)
    task = TaskMeta.objects.get_task("ticker")
    task_status = MyTask.AsyncResult("ticker")

You can choose a recurring date instead of a duration::

    from celery.task.schedules import crontab

    @periodic_task(run_every=crontab(hour=21, minute=30, day_of_week=1))
    def every_monday_night():
        print("Execute every Monday at 9:30PM.")
        
More examples: http://ask.github.com/celery/getting-started/periodic-tasks.html

Resend alert in case of failure
------------------------------------

Alerts may not work. For example, you may need to access the network
to fetch required data but it's down. You can try a tasks, then if it fails, schedule
a retry::

    @task()
    def update_remote_database(*args, **kwargs):
    
        try:
            update_remote_database()
        except Exception, e:
            update_remote_database.retry(args=args, 
                                         kwargs=kwargs, 
                                         exc=e,
                                         countdown=3600 # retry in 1 hour 
                                         )

   
Cancelling alerts
------------------------

If some reminder is not needed, you can just revoke it::

    from celery.task.control import revoke
    revoke(task_id)

However, it's usually better to just use a test in the task to check if it 
needs to perform or not.

If case of emergency, you can discard all of them::

    from celery.task import discard_all
    discard_all()

    
Tricks
=================

If you don't need the result back, set ignore_result=True to save ressources::

    @task()
    def foo(ignore_result=True):
        clear_cache() # imaginary process

You can use @tasks() on ordinary methods, but you must do a little more work.

    #. First, you must register the task::

        class Test(object):

            @task()
            def foo(self):
                self.do_stuff()
                
        from celery.registry import tasks
        tasks.register(Test.foo)

    #. Secondly, tasks won't pass ``self``, you must do it manually::

        t = Test()
        s = t.foo.delay(t) # we pass the Test instance to it's own method
        
    And you can't do that with recurring tasks...

You can debug alerts by printing, if *celeryd* use the ``-l info`` option,
you'll see it. But you can use celery logger as well::

 logger = self.get_logger(**kwargs)
        logger.info("Adding %s + %s" % (x, y))


Good practices
===========================

#. Test for failure and retry. Context may have changed in the meantime.
#. Set a condition in the task to abort. Data may have changed in the meantime.
#. Update querysets and models objets in the task code if you pass them as parameters.
   Indeed, the database may have changed but your object didn't.  
