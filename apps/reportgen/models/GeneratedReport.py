#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os
import os.path

from celery.task.control import revoke

from django.db import models
from django.db.models.signals import pre_delete
from django.utils.translation import ugettext as _

from reportgen import utils

GENERATED_DIR = 'ondemand'
PATH_TO_REPORTS = os.path.join(os.path.dirname(__file__),\
    '..', 'static', GENERATED_DIR)
'''
GeneratedReport holds information about
a one-off report that was generated on demand.

There is info on the task status, the
sort of report that was generated, and
where to find the finished report file.
'''

class GeneratedReport(models.Model):
    GENERATED_DIR = GENERATED_DIR

    TASK_STATE_PENDING  = 1
    TASK_STATE_STARTED  = 2
    TASK_STATE_RETRYING = 3
    TASK_STATE_FAILED   = 4
    TASK_STATE_SUCCEEDED = 5

    TASK_STATE_DICT = {
        TASK_STATE_PENDING      :   _("Pending"),
        TASK_STATE_STARTED      :   _("Started"),
        TASK_STATE_RETRYING     :   _("Retrying"),
        TASK_STATE_FAILED       :   _("Failed"),
        TASK_STATE_SUCCEEDED    :   _("Succeeded"),
    }

    TASK_STATE_CHOICES = (
        (TASK_STATE_PENDING,    _("Pending")),
        (TASK_STATE_STARTED,    _("Started")),
        (TASK_STATE_RETRYING,   _("Retrying")),
        (TASK_STATE_FAILED,     _("Failed")),
        (TASK_STATE_SUCCEEDED,  _("Succeeded")),
    )

    class Meta:
        app_label = 'reportgen'
        db_table = 'reportgen_generated_report'

        verbose_name = _(u"Generated Report")
        verbose_name_plural = _(u"Generated Reports")
        ordering = ('title', )
        get_latest_by = ('started_at',)
        

    report = models.ForeignKey('Report', max_length=60, blank=False, \
                                verbose_name=_(u"Report"),
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Reference to the report "\
                                    "to be generated"))
    filename = models.CharField(_(u"Filename"), max_length=255, blank=True, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Location of generated report file"))
    title = models.CharField(_(u"Title"), max_length=255, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Full title of report"))
    fileformat = models.CharField(_(u"File format"), max_length=10, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"File format of report (e.g., PDF)"))
    period_title = models.CharField(_(u"Period title"), max_length=100, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Description of the time period for "\
                                            "the report (e.g., \"January 2011\")"))
    variant_title = models.CharField(_(u"Variant title"), max_length=100, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Description of the variant for "\
                                            "the report (e.g., \"Ntungu Clinic\")"))
    task_progress = models.PositiveSmallIntegerField(_("Progress"), blank=False,
                                null=False, unique=False)
    task_state = models.PositiveSmallIntegerField(_("Task state"), blank=False,
                                null=False, unique=False, choices=TASK_STATE_CHOICES)
    task_id = models.CharField(_("Task ID"), max_length=100, blank=False, 
                                null=True, unique=False, \
                                help_text=_("The task identifier used internally "\
                                            "by RabbitMQ and celeryd to identify the "\
                                            "task used to generate this report."))
    started_at = models.DateTimeField(_("Started at"))
    finished_at = models.DateTimeField(_("Finished at"), null=True)
    error_message = models.TextField(_("Error message"), null=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return _("<Generated: %(title)s, (%(fname)s), ID: %(pk)d>") % \
            {'title': self.title, 'fname': self.filename, 'pk': self.pk}

    @property
    def is_finished(self):
        return self.task_state == self.TASK_STATE_SUCCEEDED and \
            self.filename != ''

    @property
    def is_failed(self):
        return self.task_state == self.TASK_STATE_FAILED

    @property
    def is_running(self):
        return self.task_state == self.TASK_STATE_STARTED

    @property
    def task_state_str(self):
        return self.TASK_STATE_DICT[self.task_state]

    def get_filename(self, variant, rformat):
        return self.report.get_filename(variant, rformat, self.pk)
  
    def get_filepath(self, variant, rformat):
        return os.path.join(PATH_TO_REPORTS, self.get_filename(variant, rformat))

    @property
    def file_size(self):
        try:
            return utils.file_size(os.path.join(PATH_TO_REPORTS, self.filename))
        except OSError:
            return None

def delete_report(sender, **kwargs):
    gr = kwargs['instance']

    # Try to cancel the execution of the task
    if gr.task_id:
        revoke(gr.task_id, terminate=True)

    # Try to delete the files
    if gr.filename == '':
        return True
    fn = os.path.join(PATH_TO_REPORTS, gr.filename)
    print "Looking for <%s>" % fn
    if os.path.exists(fn):
        print "Deleting <%s>" % fn
        os.unlink(fn)
    else:
        print "no file found"

    return True

pre_delete.connect(delete_report,\
    dispatch_uid='delete_report',
    weak=False,
    sender=GeneratedReport)

