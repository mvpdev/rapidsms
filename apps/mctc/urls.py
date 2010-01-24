from django.conf.urls.defaults import *
from django.contrib import admin
import mctc.views as views

admin.autodiscover()

# an issue between Django version 1.0 and later?
# see http://code.djangoproject.com/ticket/10050
try:
    admin_urls = (r'^admin/', include(admin.site.urls))
except AttributeError:
    # Django 1.0 admin site
    admin_urls = (r'^admin/(.*)', admin.site.root)

urlpatterns = patterns('',
    admin_urls,
    url(r'^mctc/?$', views.index),
    url(r'^mctc/reports?$', views.reports),
    (r'^report/(?P<report_name>[a-z\-\_]+)/(?P<object_id>\d*)$', "mctc.views.report_view"),
    #last_30_days
    (r'^last_30_days/$', "mctc.views.last_30_days"),
    (r'^last_30_days/(?P<object_id>\d*)$', "mctc.views.last_30_days"),
    (r'^last_30_days/per_page/(?P<per_page>\d*)$', "mctc.views.last_30_days"),
    (r'^last_30_days/per_page/(?P<per_page>\d*)/(?P<d>\d*)$', "mctc.views.last_30_days"),
    #patients_by_chw
    (r'^patients_by_chw/$', "mctc.views.patients_by_chw"),
    (r'^patients_by_chw/(?P<object_id>\d*)$', "mctc.views.patients_by_chw"),
    (r'^patients_by_chw/per_page/(?P<per_page>\d*)$', "mctc.views.patients_by_chw"),
    (r'^patients_by_chw/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "mctc.views.patients_by_chw"),
    #last_30_days
    (r'^measles_summary/$', "mctc.views.measles_summary"),
    (r'^measles_summary/(?P<object_id>\d*)$', "mctc.views.measles_summary"),
    (r'^measles_summary/per_page/(?P<per_page>\d*)$', "mctc.views.measles_summary"),
    (r'^measles_summary/per_page/(?P<per_page>\d*)/(?P<d>\d*)$', "mctc.views.measles_summary"),
    #patients_by_chw
    (r'^measles/$', "mctc.views.measles"),
    (r'^measles/(?P<object_id>\d*)$', "mctc.views.measles"),
    (r'^measles/per_page/(?P<per_page>\d*)$', "mctc.views.measles"),
    (r'^measles/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "mctc.views.measles"),
    #patients_by_chw
    (r'^malaria/$', "mctc.views.malaria"),
    (r'^malaria/(?P<object_id>\d*)$', "mctc.views.malaria"),
    (r'^malaria/per_page/(?P<per_page>\d*)$', "mctc.views.malaria"),
    (r'^malaria/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "mctc.views.malaria"),
    #patients_by_chw
    (r'^malnut/$', "mctc.views.malnut"),
    (r'^malnut/(?P<object_id>\d*)$', "mctc.views.malnut"),
    (r'^malnut/per_page/(?P<per_page>\d*)$', "mctc.views.malnut"),
    (r'^malnut/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "mctc.views.malnut"),
    #patients_by_chw
    (r'^trend/$', "mctc.views.trend"),
    (r'^trend/(?P<object_id>\d*)$', "mctc.views.trend"),
    (r'^trend/per_page/(?P<per_page>\d*)$', "mctc.views.trend"),
    (r'^trend/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "mctc.views.trend"),
    #patients_by_age
    (r'^List_Enfant_Age/$', "mctc.views.patients_by_age"),
    (r'^List_Enfant_Age/(?P<object_id>\d*)$', "mctc.views.patients_by_age"),
    (r'^List_Enfant_Age/per_page/(?P<per_page>\d*)$', "mctc.views.patients_by_age"),
    (r'^List_Enfant_Age/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "mctc.views.patients_by_age"),
    # commands shortlist
    (r'^mctc/commands-shortlist', "mctc.views.commands_pdf"),
    #malnutrition_screening
    (r'^malnutrition_screening/$', "mctc.views.malnutrition_screening"),
)

