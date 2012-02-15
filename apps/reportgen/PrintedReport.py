#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

import os.path
import shutil
import inspect
from datetime import datetime

from celery.task import Task
from celery.schedules import crontab

from django import db
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from django.http import HttpResponseRedirect, HttpResponseNotFound

from reportgen.models import Report, GeneratedReport

class PrintedReport(Task):
    """
    The class defining a PrintedReport.

    Whenever you make a new printed report you will
    have to define a new class that inherits from 
    this report.
    """

    title = None
    """ Human-readable title of report"""

    filename = None
    """Filename alphanumeric, underscore, and hyphen are ok """

    formats = []
    """A list of file formats to use, e.g., ['pdf','html','xls']"""

    variants = [
    ]
    """
    A list of report variants in the form::

        (title_suffix, fn_suffix, variant_data) 

    For example, you might have a patient register
    for Bugongi and Ruhiira health centers::

        variants = [
            (' Bugongi HC', '_BG', {'clinic_id': 13}),
            (' Ruhiira HC', '_RH', {'clinic_id': 15}),
        ]

    Neither the title nor filename suffixes can be 
    the empty string ""
    """

    def generate(self, time_period, rformat, title, filepath, data):
        """
        You should implement the generate method in a report
        subclass.  This method creates the report and saves it
        to the right place (probably 
        :file:`static/reports/filename.format`).
        The return value is ignored.
        """
        raise NotImplementedError(\
            _(u'Generate function not implemented.'))

    ####################
    # Unless you're an expert, you don't need to override
    # any of the rest of the methods in your subclass

    track_started = True
    abstract = True

    @property
    def classname(self):
        """Name of the file where this report is defined (e.g., 
        :class:`Operational`
        if the file is :file:`Operational.py`)
        """
        return os.path.basename(inspect.getfile(self.generate))[0:-3]

    def run(self, *args, **kwargs):
        print "Args: %s" % str(args)
        print "Kwargs: %s" % str(kwargs)
        print "Cur: %s" % get_language()
        activate(settings.LANGUAGE_CODE)
        print "Language: %s" % settings.LANGUAGE_CODE

        self.check_sanity()

        # get Report object for this report
        try:
            kwargs['report'] = Report.objects.get(classname=self.classname)
        except Report.DoesNotExist:
            raise DBConfigurationError(_("Could not find DB record "\
                "for a report with classname %s" % self.classname))

        if 'time_period' not in kwargs:
            raise ValueError(_('No time period value passed in'))

        print "Running ondemand"
        kwargs['run'] = self._run_ondemand
        kwargs['dir'] = GeneratedReport.GENERATED_DIR
        self._run_ondemand(*args, **kwargs)

    def test(self, time_period, rformat):
        """
        Use this method to test your reports from
        the shell.

        :param time_period: An object with ``start`` and
                             ``end`` methods that 
                             return :class:`datetime` objects.
        :param rformat: A string giving the report format to
                        generate (e.g., "pdf")
        """

        activate(settings.LANGUAGE_CODE)

        fname = "/tmp/test_%s.%s" % (self.filename, rformat)
        print "Saving as \"%s\"" % fname

        if self.variants:
            title = self.title + ": " + self.variants[0][0]
            data = self.variants[0][2]
        else:
            title = self.title
            data = {}

        return self.generate(time_period, rformat, title, fname, data)

    def check_sanity(self):
        if len(self.formats) == 0:
            raise ValueError(\
                _(u'This report has no formats specified.'))
        
        if self.title is None or self.filename is None \
                or len(self.title) == 0 or len(self.filename) == 0:
            raise ValueError(\
                _(u'Report title or filename is unset.'))

    def set_progress(self, progress):
        """
        Call this to update the progress of the report
        in the database.

        :param progress: A number from 0 to 100 giving the percentage
                         completion.
        :type progress: float
        """
        # Clear query cache to keep Django from
        # eating all of the memory
        db.reset_queries()

        if not hasattr(self, '_kwargs'):
            return

        kwargs = self._kwargs

        print "> Progress %d%% (at %s)" % (progress, datetime.now())

        print "Working on saving"
        kwargs['generated_report'].task_state = GeneratedReport.TASK_STATE_STARTED
        kwargs['generated_report'].task_progress = progress
        kwargs['generated_report'].save()

    def _run_ondemand(self, *args, **kwargs):
        print "[Ondemand args] %s" % str(args)
        print "[Ondemand kwargs] %s" % str(kwargs)
        # Run report for a single format and
        # a single variant for a single time
        # period
 
        # Check if a format was passed in
        rformat = kwargs.get('rformat')
        if rformat is None:
            raise ValueError('No report format requested.')
        if rformat not in self.formats:
            raise ValueError('Invalid report format requested.')

        # Check if a variant was passed in
        variant = kwargs.get('variant')
        if variant is None:
            variant = ('', None, {})

        this_data = variant[2]
        # Once the PK is set, we can get the filename for the report
        kwargs['generated_report'].filename = self.get_filename(kwargs, variant[1], rformat)
        kwargs['generated_report'].task_id = kwargs['task_id']
        kwargs['generated_report'].save()

        self._kwargs = kwargs

        # Generate the report
        self.generate(kwargs['time_period'],
                    rformat,
                    self.title + ": " + variant[0],
                    self.get_filepath(kwargs, variant[1], rformat),
                    this_data)

    def on_success(self, retval, task_id, args, kwargs):
        if 'generated_report' not in kwargs:
            print "Couldn't find generated report record"
            return

        kwargs['generated_report'].finished_at = datetime.now()
        kwargs['generated_report'].task_state = GeneratedReport.TASK_STATE_SUCCEEDED
        kwargs['generated_report'].task_progress = 100
        print "SUCCESS!!!"
        kwargs['generated_report'].save()
        
    def on_failure(self, exc, task_id, args, kwargs, einfo=None):
        print "FAILED!!!"
        print einfo

        print "Failed kwargs: (%s)" % (str(kwargs))
        if not kwargs.get('generated_report'):
            print "No generated report found"
            return 
        kwargs['generated_report'].finished_at = datetime.now()
        kwargs['generated_report'].task_state = GeneratedReport.TASK_STATE_FAILED
        kwargs['generated_report'].task_progress = 0
        
        if einfo is not None:
            kwargs['generated_report'].error_message = einfo.traceback
        kwargs['generated_report'].save()
        
    def get_filename(self, kwargs, suffix, rformat):
        return kwargs['generated_report'].get_filename(suffix, rformat)

    def get_filepath(self, kwargs, suffix, rformat):
        return kwargs['generated_report'].get_filepath(suffix, rformat)

class DBConfigurationError(Exception):
    pass
