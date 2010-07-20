******************
Installing Celery
******************


Dependancies on Ubuntu 10.04
==============================

::

    sudo aptitude rabbitmq-server
    easy_install django-celery


For date management::

    easy_install python-dateutil

Setting up the message broker
==============================

The easy way: use MYSQL
--------------------------------

For our usage, we can perfectly (and should on findtb) use MYSQL as our message broker.
It's easy to set up and sufficient::

    easy_install ghettoq
    

The champion's way: use RabbitMQ
---------------------------------

If you want to use RabbitMQ, which is faster and more reliable, and includes
more features:

Create user, a virtual host, and gives all permissions to that user::

    sudo rabbitmqctl add_user myuser mypassword
    sudo rabbitmqctl add_vhost myvhost
    sudo rabbitmqctl set_permissions -p myvhost myuser "" ".*" ".*"

Check it works::

    sudo rabbitmqctl status

    Status of node 'rabbit@your_local_host_name' ...
    [{running_applications,[{rabbit,"RabbitMQ","1.7.2"},
                            {mnesia,"MNESIA  CXC 138 12","4.4.12"},
                            {os_mon,"CPO  CXC 138 46","2.2.4"},
                            {sasl,"SASL  CXC 138 11","2.1.8"},
                            {stdlib,"ERTS  CXC 138 10","1.16.4"},
                            {kernel,"ERTS  CXC 138 10","2.13.4"}]},
     {nodes,['rabbit@your_local_host_name']},
     {running_nodes,['rabbit@your_local_host_name']}]
    ...done.

Start/Stop/restart can be done using "service".

Setting up Django-Celery
========================

#. Add *djcelery* to ``INSTALLED_APPS``.

#. Create the celery database tables::

      ./rapidsms syncdb
      
    You can use syncdb even with *South*, as celery is not registered in the migration
    process.

#. Configure the broker settings, by adding the following to your ``settings.py``

    If you use RabbitMQ::
        
        BROKER_HOST = "localhost"
        BROKER_PORT = 5672
        BROKER_USER = "myuser"
        BROKER_PASSWORD = "mypassword"
        BROKER_VHOST = "myvhost"
        
    If you use MySQL::
    
        INSTALLED_APPS = ("ghettoq", )
        CARROT_BACKEND = "ghettoq.taproot.Database"

    Then::
    
        ./rapidsms syncdb
    
#. If you don't use rate limits (we have no reason to with alerts), set to improve perfs::

    CELERY_DISABLE_RATE_LIMITS = True

#. Add the following to the .wsgi file::

    import os
    os.environ["CELERY_LOADER"] = "django"
    
#. Run::

    ./rapidsms celeryd -B
    
There is no way to detach the process, so use an utility like "stop-start-daemon"
to daemonize: http://celeryproject.org/docs/cookbook/daemonizing.html.

Use ``-l info`` to get more debugs info. ``-B`` starts the recurring tasks server.

Documentation
================

* Djangoc-celery: 
    * General: http://www.celeryq.org/docs/django-celery/getting-started/first-steps-with-django.html
    * Setting: http://celeryq.org/docs/configuration.html (in settings.py)
* Celery: http://ask.github.com/celery/getting-started/introduction.html
* RabbitMQ: 
    * General: http://www.rabbitmq.com/documentation.html
    * Setting: http://www.rabbitmq.com/install.html (in /etc/rabbitmq/rabbitmq.conf)
* dateutil: http://labix.org/python-dateutil#head-2f49784d6b27bae60cde1cff6a535663cf87497b


