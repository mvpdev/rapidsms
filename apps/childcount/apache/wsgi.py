import os
import sys


filedir = os.path.dirname(__file__)

rootpath = os.path.join(filedir, "..", "..","..") 
sys.path.append('/usr/local/lib/python2.6/dist-packages/rapidsms')
sys.path.append('/usr/local/lib/python2.6/dist-packages')
sys.path.append('/home/rapidsms/dev/sms')
sys.path.append('/home/rapidsms/dev/sms/apps/childcount')
sys.path.append('/home/rapidsms/dev/sms/apps/webapp')
sys.path.append(os.path.join(rootpath))
sys.path.append(os.path.join(rootpath,'apps'))
sys.path.append('/usr/local/lib/python2.6/dist-packages/rapidsms/webui')



os.environ['RAPIDSMS_INI'] = os.path.join(rootpath,'local.ini')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rapidsms.webui.settings'
os.environ["RAPIDSMS_HOME"] = '/usr/local/lib/python2.6/dist-packages/rapidsms'

from rapidsms.webui import settings

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
