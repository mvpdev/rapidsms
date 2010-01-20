import os


sys.path.append('/user/local/lib/python2.6/dist-packages/rapidsms')
os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

